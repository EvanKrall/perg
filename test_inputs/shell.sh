#!/bin/bash

grep 'foo .* baz' </dev/null
var="something"

echo "Thing1: ${thing1}, thing2: $thing2" $thing3

echo "${thing3[@]}"


if [[ $var == foo\ *\ baz ]]; then
	:
fi