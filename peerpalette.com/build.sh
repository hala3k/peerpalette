#!/bin/sh
cd $(dirname $0)
sass --style compressed --update .:./static;
for f in *.js; do
java -jar ../tools/yuicompressor-2.4.2.jar $f -o static/$f
done
