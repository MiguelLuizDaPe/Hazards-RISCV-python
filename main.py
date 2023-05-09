# NOP = '0'*25 + '0010011'
NOP = 'nop'
U_TYPE = 0
I_TYPE = 1
R_TYPE = 2
BS_TYPE = 3

def arrayficador(lines) -> list[str]:
  codearr = []
  for line in lines:
    code = line[:32]
    codearr.append(code)
  return codearr

def getOpcode(instruction:str) -> str:
  return instruction[25:]

def getRd(instruction:str):
  return instruction[20:25]

def getRs1(instruction:str):
  return instruction[12:17]

def getRs2(instruction:str):
  return instruction[7:12]

def descobreTipo(code:str) -> int:
  opcode = getOpcode(code)
  
  match opcode: #verifica o tipo de comando do binario
    case '0110111'|'0010111'|'1101111': #lui, auipc, jal 
      return U_TYPE
    case '1100111'|'0000011'|'0010011': #jalr, L-type, I-type
      return I_TYPE
    case '0110011': #R-type
      return R_TYPE
    case '1100011'|'0100011': #B-type, S-type
      return BS_TYPE
    case _:
      return -1

def fmtInstrucao(ins:str) -> str:
  t = descobreTipo(ins)
  if t == U_TYPE:# U-TYPE ou JAL
    return f'[U]:    {ins[:20]}|{getRd(ins)}|{getOpcode(ins)}'
  elif t == I_TYPE: # JALR OU LTYPE OU JTYPE
    return f'[I]:  {ins[:12]}|{getRs1(ins)}|{ins[17:20]}|{getRd(ins)}|{getOpcode(ins)}'
  elif t == R_TYPE:
    return f'[R]: {ins[:7]}|{getRs2(ins)}|{getRs1(ins)}|{ins[17:20]}|{getRd(ins)}|{getOpcode(ins)}'
  elif t == BS_TYPE:
    # NOTE: nao tem rd, mas eh o msm range, entao tanto faz.
    return f'[BS]:{ins[:7]}|{getRs2(ins)}|{getRs1(ins)}|{ins[17:20]}|{getRd(ins)}|{getOpcode(ins)}'
  else:
    return f'[?]: --------------------------------'

# Checa se existe hazard entre as instrucoes localizadas nos indices a e b
def temDependencia(instructions:list[str], a:int, b:int) -> bool:
  rd = getRd(instructions[a])
  iT = descobreTipo(instructions[b])

  if iT == I_TYPE:
    rs1 = getRs1(instructions[b])
    if rd == rs1:
      print(f'Dep entre:\n\t{fmtInstrucao(instructions[a])}  ({a})\n\t{fmtInstrucao(instructions[b])}  ({b})')
      return True
  elif (iT == R_TYPE) or (iT == BS_TYPE):
    rs1 = getRs1(instructions[b])
    rs2 = getRs2(instructions[b])
    if rd == rs1 or rd == rs2:
      print(f'Dep entre:\n\t{fmtInstrucao(instructions[a])}  ({a})\n\t{fmtInstrucao(instructions[b])}  ({b})')
      return True

  return False

def bubbleSemFow(codearr:list[str]) -> list[str]:
  arrPronto = []    
  
  for i, code in enumerate(codearr):
    arrPronto.append(code)
    tipo = descobreTipo(code)

    match tipo:
      case 0 | 1 | 2:
        rd = getRd(code)
        if rd == '0' * 5:
          continue
        try:
          if temDependencia(codearr, i, i+1):
            arrPronto.append(NOP)
            arrPronto.append(NOP)
          elif temDependencia(codearr, i, i+2):
            arrPronto.append(NOP)
        except IndexError:
          pass
      case _:
        continue
  return arrPronto

def bubbleComFow(codearr:list[str]) -> list[str]:
  arrPronto = []    

  for i, code in enumerate(codearr):
    arrPronto.append(code)
    tipo = descobreTipo(code)
    
    match tipo:
      case 0 | 1 | 2:
        rd = getRd(code)
        if rd == '0' * 5:
          continue
        try:
          if temDependencia(codearr, i, i+1):
            arrPronto.append(NOP)
        except IndexError:
          pass
      case _:
        continue
  return arrPronto

# Cicla fatia de lista nos indices (a, b) inclusos.
  # a b c d e f g
  # tmp = e
  # a |e b c d| f g
def ciclarFatia(l:list, a:int, b:int):
  tmp = l[b]
  while b > a:
    l[b] = l[b-1]
    b -= 1
  l[a] = tmp

#Checa se tem um B-type, jal ou jalr no meio, se tiver não troca pq fode a lógica do programa
def temProibidoNoMeio(codearr:list[str], a:int, b:int) -> bool:
  BTYPE = '1100011'
  JAL = '1101111'
  JALR = '1100111'
  for i in range(a, b+1):
    op = getOpcode(codearr[i])
    print(f'[{i}] OP:{op} : {codearr[i]}')
    if (op == BTYPE) or (op == JAL) or (op == JALR):
      print(f'ESSE TA IMPEDINDO A TROCA -> {codearr[i]}')
      return True

  return False
	
#se codearr[a] == codearr[b] não vai rodar
def temDependenciaNoMeio(codearr:list[str], a:int, b:int) -> bool:
  # off by one?
  for i in range(a, b):
    if temDependencia(codearr, b, i): 
        return True
  return False

# a b [c {d] (e} f) g
#         i      j

#mudar essa porra
def reordenar(codearr:list[str], i:int) -> None:

  # enquanto ele não passar por B-type, jal ou jalr é pra ele continuar procurando até acabar
  j = i+2

  while True:

    daPraTrocar = not (temDependencia(codearr, i, j) or temDependencia(codearr, i+1, j))
    if daPraTrocar:
      print(f'Cycling {i+1} and {j}')
      if temProibidoNoMeio(codearr, i+1, j) or temDependenciaNoMeio(codearr, i+1, j):
        return
      ciclarFatia(codearr, i+1, j)
      return
  
    j += 1

def reordenarComFow(codearr:list[str]) -> list[str]:  
  for i, code in enumerate(codearr):
    tipo = descobreTipo(code)
    proxTipo = -1
    try:
      proxTipo = descobreTipo(codearr[i+1])
    except IndexError:
      pass

    permiteAtual = ((tipo == U_TYPE) or (tipo == I_TYPE) or (tipo == R_TYPE))
    permiteProximo = ((proxTipo == U_TYPE) or (proxTipo == I_TYPE) or (proxTipo == R_TYPE))
    if permiteAtual and permiteProximo:
      rd = getRd(code)
      if rd == '0' * 5:
        continue
      try:
        if temDependencia(codearr, i, i+1): 
          reordenar(codearr, i)
      except IndexError:
        pass
    else:
      continue

  codearr = bubbleComFow(codearr)
  return codearr

def main():
  # Lê o arquivo de memória de instrução em hexadecimal ou binário
  filedata = []
  with open("ex01.txt", "r") as f:
    filedata = arrayficador(f.readlines())

  # print('==== BUBBLE (NO FWD) ====')
  # fixed = bubbleSemFow(filedata)
  # for i, ins in enumerate(fixed):
  #   print(f'{i:3} {fmtInstrucao(ins)}')

  # print('==== BUBBLE (FWD) ====')
  # fixed = bubbleComFow(filedata)
  # for i, ins in enumerate(fixed):
  #   print(f'{i:3} {fmtInstrucao(ins)}')
  
  print('==== ORIGINAL ====')
  for i, ins in enumerate(filedata):
    print(f'{i:3} {fmtInstrucao(ins)}')
  
  print('==== REORDENADO (FWD) ====')
  fixed = reordenarComFow(filedata)
  for i, ins in enumerate(fixed):
    print(f'{i:3} {fmtInstrucao(ins)}')

if __name__ == '__main__': main()
