<start> ::= <magic> <length> <payload>
<magic> ::= <magic_byte1> <magic_byte2>
<magic_byte1> ::= <byte>
<magic_byte2> ::= <byte>
<length> ::= <byte>
<payload> ::= <byte>+
<byte> ::= <bit>{8}
<bit> ::= "0" | "1"

# 1. Somma dei due magic byte in un range
where 100 <= int(str(<magic_byte1>), 2) + int(str(<magic_byte2>), 2) <= 300

# 2. magic_byte1 multiplo di 4
where int(str(<magic_byte1>), 2) % 4 == 0

# 3. magic_byte2 multiplo di 5
where int(str(<magic_byte2>), 2) % 5 == 0

# 4. Payload: nessun byte nullo, almeno 2 zeri per byte
where forall <b> in <payload>.<byte>: str(<b>) != "00000000"
where forall <b> in <payload>.<byte>: str(<b>).count("0") >= 2

# 5. Dipendenza globale tra lunghezza del payload e byte <length>
where len(str(<payload>)) % 256 == int(str(<length>), 2) * 8
