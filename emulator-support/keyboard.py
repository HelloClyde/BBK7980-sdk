"""7980 matrix positions from the stock firmware table at NOR offset 0xfd67."""
KEYS={'Up':57,'Down':59,'Left':51,'Right':58,'Return':50,'Escape':49,
      'Prior':42,'Next':43,'F1':44,'F2':45,'F3':46,'F4':47,'F5':48,
      'Delete':56,'BackSpace':54,'Home':52,'space':34,'Shift_L':21,'Shift_R':21,
      'Control_L':32,'Control_R':32}
for text,start in [('1234567890',0),('qwertyuiop',11),('asdfghjkl',23),('zxcvbnm',35)]:
    for index,character in enumerate(text):
        KEYS[character]=start+index
        if character.isalpha():KEYS[character.upper()]=start+index
