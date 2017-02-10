#!/bin/bash
# You need pandoc to actually convert Markdown to reStructured Text
echo "Creation du repertoire tmp"
mkdir tmp
cd tmp

echo "Split du Readme selon les catégories"
csplit ../README.md '/^#[^#]/' '{*}'
rm xx00

echo "Exportation des catégories en doc rest"
for file in `ls`
do
	fileNameHash=`cat $file | grep "^#[^#]"`
	echo $fileNameHash
	fileName=${fileNameHash#\#}  
	mv $file "$fileName.md"
	pandoc --from=markdown --to=rst --output=../docs/readme/"$fileName.rst" "$fileName.md"
	SUCCESS=$?
done

echo "Conversion réussie"
if [ $SUCCESS -eq 0 ]
then
	echo "Suppression des fichiers temporaires"
	rm *
	cd ../docs/readme/
	rmdir ../../tmp/


	echo "Suppression des espaces dans les fichiers"
	for f in *\ *; do mv "$f" "${f// /_}"; done

	echo "Remplacement des liens"
	sed -i 's:docs/:../:g' *.rst

	echo "Compilation de la documentation HTML"
	cd ../
	make html
fi
