#!/bin/bash

grep 'foo .* baz' </dev/null
var="something"

if [[ $var == foo\ *\ baz ]]; then
	:
fi