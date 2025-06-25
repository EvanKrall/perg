#!/bin/bash

grep 'foo .* baz' </dev/null
var="something"

echo -en "Thing1: ${thing1}, thing2: $(thing2)" $thing3
echo ab"c${d}"$(echo "e" f)$'g'
echo "${thing3[@]}"
echo $hi $(echo hello)
echo a\ b\ c


cat <<<"Hello, $name, how are you?"

cat <<END
Hello, $name, how are you?
I am well today, thanks for asking, $name.
END

cat <<"EOF"
Hello, $name, how are you?
I am well today, thanks for asking, $name.
Hello, *, how are you?
EOF

if [[ $var == foo\ *\ $baz ]]; then
	:
fi
