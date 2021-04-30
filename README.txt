Pour commencer, c'est suffit de lancer le fichier code_final.py
Pour tester sur un des tests, changer les 2 lignes signal_path et cr_path en 2 chemins correspondants


L'interface va apparaitre:

Partie gauche:
Bouton Start: Commencer l'enregistrement des données
Champ Nb_trames: Indiquer le nombre de trames pour l'enregistrement

Partie droite:
Bouton Plot: Tracer le plot de la donnée brute.
NOTE: Le plot ici est celui de la donnée indiquée sur signal_path et cr_path
Si vous voulez de tracer le plot après l'enregistrement, mettez signal_path et cr_path à "./donnees_try.csv"
et "./changed_regime_time.csv".

Bouton Algo 1,2,3,4: Appliquer des algos sur le signal indiqué dans signal_path.
Algo 1: Algo time
Algo 2: Algo nb
Algo 3: Algo autocorr
Algo 4: Algo intercorr

Bouton CHANGER DE FREQUENCE: Pendant l'enregistrement, appuyez sur ce bouton pour indiquer le moment du changement de 
régime.

Bouton Disconnect: Quitter l'interface.


Il y a aussi 2 fichiers test_results qu'on a faits. Ces 2 fichiers contiennent des cas de tests intéressants.
Fichier de Bach: Tests sur l'algo 1,2,3
Fichier de Cornelius: Test sur l'algo 4


On ne peut pas créer à temps un script pour refaire tous ces tests alors il faut les refaire à la main. Désolé :(

