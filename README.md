# Practica_2
Este repositorio contiene los documentos que desarrollan la segunda practica obligatoria de la asignatura de programación paralela.
En ella se nos pide desarrollar un código utilizando la biblioteca multiprocesing de python que resuelva el problema del punte de Ambite.
La anchura del puente no permite el paso de vehículos en ambos sentidos. Por motivos de seguridad los peatones y los vehículos no pueden 
compartir el puente. En el caso de lospeatones, sí que que pueden pasar peatones en sentido contrario.

El repositorio incluye un archivo pdf donde se explica un esquema a mano de como se va a resolver el problema utilizando pseudocódigo.
El esquema incluye los invariantes de cada versión del código, una demostración de por qué el puente es seguro y una última versión que
resuelve razonadamente los problemas que han ido surgiendo de inanición y deadlocks.

Además, incluye un primer programa implmentado en python practica2_pr_version1.py donde desarrollo una primera idea que se limita a resolver 
el problema usando monitores sin tener en cuenta ningún otro problema que pueda aparecer.

Por último, adjunto el programa practica2_pr.py donde desarrollo un sistema de turnos que se van alternando de manera rotativa como solución a los problemaas de inanición y deadlocks que aparecían en la primera versión del programa.
