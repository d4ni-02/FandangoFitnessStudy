<start> ::= <magic> <length> <payload>
<magic> ::= <magic_byte1> <magic_byte2>
<magic_byte1> ::= <byte>
<magic_byte2> ::= <byte>
<length> ::= <byte>
<payload> ::= <byte>+
<byte> ::= <bit>{8}
<bit> ::= "0" | "1"

where 100 <= int(str(<magic_byte1>), 2) + int(str(<magic_byte2>), 2) <= 300

where int(str(<magic_byte1>), 2) % 4 == 0

where int(str(<magic_byte2>), 2) % 5 == 0

where forall <b> in <payload>.<byte>: str(<b>) != "00000000"
where forall <b> in <payload>.<byte>: str(<b>).count("0") >= 2

where len(str(<payload>)) % 256 == int(str(<length>), 2) * 8
