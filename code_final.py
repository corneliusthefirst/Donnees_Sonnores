import time
import threading
import serial
import os
import numpy as np
import pandas as pd
from tkinter import *
from serial.tools import list_ports
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,NavigationToolbar2Tk)
import scipy.io.wavfile as wave


trames = []
count=0
serial_object = None
countLapArray=[]
changed_regime = []
START = False
hasplotted = False
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# Path to the data for testing purposes
signal_path = "./DATA/3lines/donnees_try.csv"
cr_path = "./DATA/3lines/changed_regime_time.csv"

window = Tk()
window.title("Donnees Sonores")



# Calculate the auto-correlation of a signal
# i >= N but usually, we take i = N and M is len(x) - N
# N is the shifting value of the signal
def autocorrel(x,N,i,M):
    C = np.zeros(N)
    for k in range(i,i+M):
        for n in range(N):
            C[n] += x[k]*x[k-n]
    return C/M

def generate():
    """
    Treat the signal to obtain a timeblock. A timeblock is a list of times between
    2 signal blocks or more precisely the time where a change occurs (255 -> 0)
    or (0 -> 255)
    """
    signal = pd.read_csv(signal_path, squeeze=True, index_col=0)
    cr =  pd.read_csv(cr_path, squeeze=True, index_col=0)
    changed_regime = []
    for _,value in cr.items():
        changed_regime.append(value)
    #get all the time in a timearray and a valueArray
    timeArray = []
    valueArray = []
    for index,value in signal.items():
        timeArray.append(index)
        valueArray.append(value)

    timeBlock=[]
    before = valueArray[0]
    timeBlock.append(timeArray[0])
    i=0
    j=1
    while i < len(timeArray):
        while i < len(timeArray) and valueArray[i] == before:
            before = valueArray[i]
            i = i + 1

        if i < len(timeArray):
            before = valueArray[i]
            timeBlock.append(timeArray[i])
            j = j + 1
        else:
            timeBlock.append(timeArray[i-1])
    return timeBlock,changed_regime

def Algo_time():
    """
    Window fixed on number of rising values (fronts montants). Calculate the median
    time in each window then compare the difference between 2 windows with a threshold
    """
    timeBlock,changed_regime = generate()

    # blockLength contains the time between 2 rising values
    # We use blockLength_list to calculate, blockLength is only for examine the
    # data
    blockLength = {}
    blockLength_list = []
    n = len(timeBlock)
    i=2
    while i < n:
        blockLength[timeBlock[i-2]] = timeBlock[i]-timeBlock[i-2]
        blockLength_list.append(timeBlock[i]-timeBlock[i-2])
        i = i + 2

    # Creating the window and calculate the time median in each window
    # Results are stored in signal_traiter
    step = 50
    signal_traiter = []
    for j in range(len(blockLength_list)-step):
        sum = 0
        list_med = []
        for i in range(j,j+step):
            list_med.append(blockLength_list[i])
        list_med.sort()
        signal_traiter.append(list_med[int(step/2)])

    seuil = 0.0001

    # Since we use blockLength_list for calculations, we can only obtain the index of the
    # window where the decision is made
    # We store the indices in a list
    list_index = []
    index = 1
    while index < len(signal_traiter):
        if abs(signal_traiter[index] - signal_traiter[index-1]) >= seuil:
            list_index.append(index)
        index = index + 1

    decisionList = []

    # For each window index, retrace to calculate the decision then add it
    # to the list
    for index in list_index:
        val = 0
        for i in range(index+step+1):
            val += blockLength_list[i]
        decisionList.append(val)
    print("Threshold:",seuil)
    print("Decisions:", decisionList)
    print("Reality:", changed_regime)

def Algo_nb():
    """
    Inverse of algo time
    Window fixed on time. Count the number of rising values
    in each window then compare the difference between 2 windows with a threshold
    """
    timeBlock,changed_regime = generate()
    taille_timeBlock = len(timeBlock)

    # Creating the window then count the number of rising values
    # We simply check the time when a rising values occur, if the time is smaller
    # than the window, then increment the counter by 1
    step = 0.1
    time_range = np.arange(0,timeBlock[taille_timeBlock-1],step)
    nb_signalsArray = {}
    for k in range(len(time_range)-1):
        c = 0
        u = 0
        t_count = []
        while u < taille_timeBlock :
            if timeBlock[u] > time_range[k] and timeBlock[u] < time_range[k+1]:
                c = c + 1
                t_count.append(timeBlock[u])
            u = u + 1
        #nb_signalsArray.append(c)
        if(t_count):
            nb_signalsArray[np.mean(t_count)] = c

    # Comparing 2 windows by calculating the difference of the number
    # of rising values between them
    seuil = 60
    nb_signalsList = list(nb_signalsArray.keys())
    decisionList = []
    for i in range(1,len(nb_signalsList)-1):
        ind = nb_signalsList[i]
        ind_add_1 = nb_signalsList[i+1]
        current_diff= abs(nb_signalsArray[ind] - nb_signalsArray[ind_add_1])
        if current_diff>= seuil:
            decisionList.append(nb_signalsList[i+1])
    print("Threshold:",seuil)
    print("Decisions:", decisionList)
    print("Reality:", changed_regime)

def Algo_auto():
    """
    Use a window of size 3000 thousand values and glide on the signal.
    Calculate the autocorrelation in each window then use the norm 2 to compare
    between 2 windows. If the value is bigger than the threshold, make the
    decision there.
    """

    signal = pd.read_csv(signal_path, squeeze=True, index_col=0)
    cr =  pd.read_csv(cr_path, squeeze=True, index_col=0)
    changed_regime = []
    for _,value in cr.items():
        changed_regime.append(value)
    #get all the time in a timearray and a valueArray
    timeArray = []
    valueArray = []
    for index,value in signal.items():
        timeArray.append(index)
        valueArray.append(value)

    i=0
    # Dictionnary to store all the correlation vecteurs in form:
    # time:vecteur
    dict_corr = {}
    n = len(timeArray)
    nb_values = 3000

    while i < n - nb_values:
       temps = timeArray[i:i+nb_values]
       # shifting period, take by default nb_values/4
       period = int(nb_values/4)
       # calculate the autocorrelation of the window and store its normalisation
       # in dict_corr
       corr_data = autocorrel(valueArray[i:i+nb_values],period,period,nb_values-period)
       corr_data = corr_data /np.max(corr_data)
       dict_corr[np.mean(temps)] = corr_data
       i = i + nb_values

    # Create a final output dictionnary by calculating the norm between the difference
    # of 2 correlation vecteurs
    corr_keys = list(dict_corr.keys())
    corr_values = list(dict_corr.values())

    output_final = {}
    for i in range(len(corr_values)-1):
        val = np.subtract(corr_values[i],corr_values[i+1])
        output_final[(corr_keys[i+1] + corr_keys[i])/2] = np.linalg.norm(np.absolute(val))

    # Extract the data from output_final to compare with the threshold and make the decision
    time_output = list(output_final.keys())
    data_output = list(output_final.values())
    data_output = data_output/max(data_output)

    seuil = 0.55
    decisionList = []
    for i in range(len(data_output)-1):
        current_corr = data_output[i]
        if current_corr >= seuil:
            decisionList.append(time_output[i+1])
    print("Threshold:",seuil)
    print("Decisions:", decisionList)
    print("Reality:", changed_regime)

def Algo_inter():
    """
    Algo 4 Intercorrelation,dans cet algorithme on faits l'intercorrelation de chaque 3000 donnees avec  tous les autres données en groupe de 3000
    succesivement on garde les max pour chaque iteration avant de ramener les donnees d'intercorrelation obtenue sur l'interval (0,1)
    avant d'appliquer une moyenne sur sont temps et d'y attacher le tableau obtenue de l'intercorrelation multiple comme valeur obtenue ,et ainsi les garder dans notre dictionaire outputObject
    Apres l'obtention de ces donnees on fixe un seuil pour lequel on cherche les valuer du dictionnaire qui respecte l'ecart du seuil.A la fin on print la quantite de changement obtenue de la fin au debut du tableau de changement de regime obtenue
    Cet algorithme marche bien dans practiquement tous les cas de changement teste pour l'instant apart pour le cas de 10 changement de regimes succesive ou
    il fais des miss sur parraport a ce qui etais attendue,mais a qu'a meme a peu pres 70% de match
    """
    signal = pd.read_csv(signal_path, squeeze=True, index_col=0)
    cr =  pd.read_csv(cr_path, squeeze=True, index_col=0)
    changed_regime = []
    for _,value in cr.items():
        changed_regime.append(value)

    #get all the time in a timearray and a valueArray
    timeArray = []
    valueArray = []
    for index,value in signal.items():
        timeArray.append(index)
        valueArray.append(value)

    i=0
    dict_corr = {}
    n = len(timeArray)
    nb_values = 3000
    while i < n - 2*nb_values:
       temps = timeArray[i:i+nb_values]
       j=0
       valinit = valueArray[i:i+nb_values]
       corr_data=[]
       while j < n - 2*nb_values:
            if(j != i):
                data =   np.correlate(valinit,valueArray[j:j+nb_values],mode="same")
                corr_data.append(np.max(data))
            j = j + nb_values
       corr_data = corr_data /np.max(corr_data)
       dict_corr[np.mean(temps)] = corr_data
       i = i + nb_values


    #find the changes in this data
    corr_keys = list(dict_corr.keys())
    corr_values = list(dict_corr.values())

    output_final = {}
    for i in range(len(corr_values)-1):
        val = np.subtract(corr_values[i],corr_values[i+1])
        output_final[(corr_keys[i+1] + corr_keys[i])/2] = np.linalg.norm(np.absolute(val))
    time_output = list(output_final.keys())
    data_output = list(output_final.values())
    data_output = data_output/max(data_output)

    seuil = 0.95
    decisionList = []
    for i in range(len(data_output)):
        current_corr = data_output[i]
        if current_corr >= seuil:
            decisionList.append(time_output[i+1])
    print("Threshold:",seuil)
    print("Decisions:", decisionList)
    print("Reality:", changed_regime)

def Start():
    """
    The function initiates the Connection to the UART device with the Port and Buad fed through the Entry
    boxes in the application.

    """
    global serial_object
    x = list(list_ports.comports())
    print([port.name for port in x])
    serial_param = {'port': 'COM3',
            'baudrate': 115200,
             'parity': serial.PARITY_NONE,
            'stopbits': serial.STOPBITS_ONE,
            'bytesize': serial.EIGHTBITS,
           'timeout': 2}
    serial_object = serial.Serial(**serial_param)

    t1 = threading.Thread(target = get_data)  #start the getdata on one threadç
    t1.daemon = True
    t1.start()



def get_data():
    """
    This function serves the purpose of collecting data from the serial object and storing
    the filtered data into a global variable.
    The function has been put into a thread since the serial event is a blocking function.
    """
    global trames
    global count
    global serial_object
    # %%
    # liste les ports


    # %%
    # enregistrement de données
    taille = 551
    n_trame = int(no_tramme.get())
    try:
        # envoie le code lecture
        serial_object.write(bytes.fromhex('AA'))
        for lap in range(n_trame):
            count = lap
            print("inner count value", count)
            output = serial_object.read(int(taille))
            trames.append(np.frombuffer(output, np.uint8))
        # envoie le code fin de lecture
        serial_object.write(bytes.fromhex('55'))
    except:
        print('erreur')
    # conversion en dataframe
    print(trames)
    trames = np.array(trames)
    signal = pd.Series(trames.flatten(), index=np.arange(trames.size)/(44100))

    data = pd.DataFrame(data=signal)
    data.to_csv("donnees_try.csv", index=True)
    getChangedRegimeTime()
    # %%
    # affichage
    # signal.plot()




def disconnect():
    """
    This function is for disconnecting and quitting the application.
    """
    try:
        serial_object.close()

    except AttributeError:
        print("Closing the Gui ...")
    window.quit()

def ChangedFrequency():
    global countLapArray
    global count
    global trames
    countLapArray.append(count)
    # regime_change.append(len(trames)) get the time from the trames an push it
    print("frequency changed", changed_regime, len(trames))



def getChangedRegimeTime():  # form the array of times of each regime change based on the signal series and the different counts made at breaks
    global changed_regime
    global trames
    global countLapArray
    trames = np.array(trames)
    signal = pd.Series(trames.flatten(), index=np.arange(trames.size)/(44100))
    i = 0
    j = 0
    n = len(countLapArray)
    for index, _ in signal.items():
        if j<n and i == countLapArray[j]*551: #since a trame or step here is 551 values
            # we append the time of this regime change
            changed_regime.append(index)
            j = j + 1
        i = i + 1
    #save the change regime array to a file
    df = pd.DataFrame(changed_regime)
    df.to_csv('changed_regime_time.csv')






def plot():
    global changed_regime
    global trames
    global hasplotted

    #getChangedRegimeTime() #call this function to get the change regime time array populated

    if hasplotted == False:
        # the figure that will contain the plot
        fig = Figure(figsize=(8.5, 6.7), dpi=100)

        # adding the subplot
        plot1 = fig.add_subplot(111)

        # plotting the signal
        signal = pd.read_csv(signal_path, squeeze=True, index_col=0)
        #get the change regime data
        if len(changed_regime) == 0:
            cr =  pd.read_csv(cr_path, squeeze=True, index_col=0)
            for _,value in cr.items():
                changed_regime.append(value)

        plot1.plot(signal)
        for i in changed_regime:
            plot1.axvline(x=i, color='r', linestyle='-')
        # plot1.plot(signal)

        # creating the Tkinter canvas
        # containing the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.get_tk_widget().pack()
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().place(y=180)

        # creating the Matplotlib toolbar
        toolbar = NavigationToolbar2Tk(canvas, window)
        toolbar.pack(padx=5)
        toolbar.update()

        # placing the toolbar on the Tkinter window
        canvas.get_tk_widget().pack(side=BOTTOM, padx=5, pady=25)

        hasplotted  = True






if __name__ == "__main__":

    """
    The main loop consists of all the window objects and its placement.
    The Main loop handles all the widget placements.
    """
    Frame(height = 120, width = 890, bd = 3, relief = 'groove').place(x = 5, y = 5)
    text = Text(width = 65, height = 5)


    start_button = Button(window, text='START', command=Start)
    Algo_time_button = Button(window, text='ALGO1', command=Algo_time)
    Algo_nb_button = Button(window, text='ALGO2', command=Algo_nb)
    Algo_auto_button = Button(window, text='ALGO3', command=Algo_auto)
    Algo_inter_button = Button(window, text='ALGO4', command=Algo_inter)


    frequence_button = Button(window, text='CHANGER DE FREQUENCE', command=ChangedFrequency)


    no_tramme = Spinbox(window, from_=0, to=1000, width=7)

    plot_button = Button(window, command=plot, height=1, width=10, text="Plot")

    disconnect = Button(window, text = "Disconnect", command = disconnect)

    text = Label(text="Nb_trame", font=(30))


    # place the button
    # in main window
    start_button.pack(side=TOP, padx=5, pady=10)
    start_button.place(x=10, y=15)

    text.pack(side=TOP, padx=5, pady=10)
    text.place(x=10, y=70)

    no_tramme.pack(side=TOP, padx=5, pady=10)
    no_tramme.place(x=100, y=70)


    frequence_button.pack(side=TOP, padx=5, pady=5)
    frequence_button.pack(side=RIGHT)
    frequence_button.place(x=675, y=15)

    plot_button.pack(side=TOP, padx=5, pady=5)
    plot_button.place(x=540, y=15)

    disconnect.place(x =775, y = 55)
    Algo_time_button.place(x=600,y=55)
    Algo_nb_button.place(x=680,y=55)
    Algo_auto_button.place(x=600,y=90)
    Algo_inter_button.place(x=680,y=90)

    #mainloop
    window.geometry('900x900')
    window.mainloop()
