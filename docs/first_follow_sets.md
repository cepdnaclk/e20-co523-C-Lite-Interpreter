###### FIRST Sets

FIRST(program) = { int, float, identifier, if, printf, {, ; }
FIRST(declaration) = { int, float }
FIRST(statement) = { identifier, if, printf, {, ; }
FIRST(expression) = { number, identifier, (, +, - }

***

###### FOLLOW Sets

FOLLOW(program) = { $ }  (end of input)
FOLLOW(statement) = { int, float, identifier, if, printf, {, }, else, ;, $ }