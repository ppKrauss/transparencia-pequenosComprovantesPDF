
# Substituir pelo path desejado, aqui só exemplo:
buscar_PDFs_aqui = "/home/peter/Downloads/Planos e finanças da família Krauss"
# Listas os nomes de arquivo PDF a serem ignorados, aqui só exemplo:
stopFiles = ["00000472-Comunição não Violenta.pdf", "meIgnore.pdf", "naoQueroLer.pdf"]
# Controles de parada e tipo de saída:
stopOnNoPattern = True
stopOnSizeError = False
outputCSV_SEP = '|' # evite mudar. Uso de '!' ou '#' seriam alternativas, ';' e ',' perigosos.

# Impor limite de bytes para um PDF de PIX e/ou Boleto.. Mas o correto é deixar isso para o texto:
minText = 1000
maxText = 20000
layoutBytes = 50000

######
# Conferir se todos os tipos de PDF (templates) necessários nesta lista:
patterns =[
    # PIX dos bancos Santander, Fulano, ...
    ("Pix", r"Comprovante\s+d[eo]\s+Pix[\s\n\r]+(.+)[\s\n\r]+Valor pago[\s\n\r]+.+[\s\n\r]+"),
    # criar Pix2, Pix3, etc. para outros templates
    #r"Comprovante\s+d[eo]\s+(Pix)[\s\n\r]+(.+)[\s\n\r]+Valor pago[\s\n\r]+(.+)[\s\n\r]+Forma de pagamento[\s\n\r]+(.+)[\s\n\r]+.*Dados do recebedor[\s\n\r]+Para[\s\n\r]+(.+)",
    ("Pagamento", r"Comprovante\s+d[eo]\s+Pagamento[\s\n\r]+(.+)[\s\n\r]+"),
    ("TED", r"Comprovante\s+d[ea]\s+(Transferência)[\s\n\r]+(.+)[\s\n\r]+"),
    ("Outros", r"(Claro NXT Telecomunicações|Documento de Arrecadação|Comprovante d[eo] [aA]gendamento|Recomendamos a impressão desse Comprovante)")
]
emissorPatterns = [ # texto caracterizador do banco em geral no final ou rodapé do PDF:
   ('Santander', r"[Cc]entral\s+de\s+[Aa]tendimento\s+Santander"), # em Pix
   ('Bradesco', r"Alô\s+Bradesco")
]
pixPatterns= {} # usar emissores.
pixPatterns['generico'] = [
  ('valor_pago', r"Valor pago[\s\n\r]+(.+)[\s\n\r]+"),
  ('forma_pgmnto', r"Forma de pagamento[\s\n\r]+(.+)[\s\n\r]+"),
  ('para_recebedor', r"Dados do recebedor[\s\n\r]+Para[\s\n\r]+(.+)"),
  ('info_recebedor', r"Informação para o recebedor[\s\n\r]+(.+)[\s\n\r]+"),
  ('ignorado1', r"")
]
pixPatterns['Santander'] = [
  ('valor_pago', r"Valor pago[\s\n\r]+(.+)[\s\n\r]+"),
  ('forma_pgmnto', r"Forma de pagamento[\s\n\r]+(.+)[\s\n\r]+"),
  ('para_recebedor', r"Dados do recebedor[\s\n\r]+Para[\s\n\r]+(.+)"),
  ('info_recebedor', r"Informação para o recebedor[\s\n\r]+(.+)[\s\n\r]+"),
  ('ignorado1', r"")
]

csv_header = 'ID|doc_tipo|doc_emissor|doc_fileName|doc_sha1|doc_file_date|reg_data|reg_status|reg_valor|para_conta|para_nome|para_info|etc'

# CSV with pipes:
# id|tipo_comprovante|arquivo_nome|arquivo_sha1sum|data|

##############
import pypdf  # or PyPDF2
import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime

folder_path = Path(buscar_PDFs_aqui)
globStop = False
minBytes = minText*2 + layoutBytes
maxBytes = maxText*2 + layoutBytes*2


def get_sha1_subprocess(file_path):
    result = subprocess.run(['sha1sum', file_path], capture_output=True, text=True)
    return result.stdout.split()[0]

def extract_SEP(text):
    return str(text).replace(outputCSV_SEP, '-')

def extract_br_date(text):
	match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
	if match:
	    return str(
	      datetime.strptime(match.group(0), '%d/%m/%Y')
	    )[0:10]
	else:
	    return text

def extract_patterns(label_pattern_pairs, text, retLabel=False):
    valores=[]
    for rotulo, xpat in label_pattern_pairs:
        if not xpat:
            valores.append('')
            continue
        m = re.search(xpat, text)
        if retLabel:
            valores.append(rotulo if m else '')
        else:
            v = m.group(1).strip() if m and m.lastindex else ''
            #extract_SEP(v) if rotulo.startswith("info") else v
            valores.append( extract_SEP(v) )
    return valores


def getPixPdf(file,id):
    global globStop, patterns, minText, maxText, maxBytes, stopOnNoPattern, stopOnSizeError
    retVals = []  # for CSV returns

    with open(file, "rb") as arquivo_pdf:
        lenBytes = file.stat().st_size
        # file_date_create = datetime.fromtimestamp( file.stat().st_ctime ).date().isoformat()  # criacao
        file_date_create = datetime.fromtimestamp( file.stat().st_mtime ).date().isoformat()  # modificacao
        # bad sha1sum = hashlib.file_digest(f,"sha1").hexdigest()
        sha1sum = get_sha1_subprocess(file)
        fileVals = [file.name,sha1sum,file_date_create]
        errVals  = [str(id),'undefined','generico']+ fileVals
        if lenBytes>maxBytes:
            print("---- Tamanho excedeu o limite de bytes ----", file=sys.stderr)
            print(" arquivo: "+file.name, file=sys.stderr)
            globStop = stopOnSizeError
            return  errVals+['','err01','','','','']
        leitor = pypdf.PdfReader(arquivo_pdf)
        # Itere por todas as páginas
        fullText = ""
        for i, pagina in enumerate(leitor.pages):
            texto = pagina.extract_text()
            fullText = fullText+texto

    lenText = len(fullText)
    if lenText>maxText:
        print("---- Tamanho excedeu o limite de caracteres no texto ----", file=sys.stderr)
        print(" arquivo: "+file.name, file=sys.stderr)
        globStop = stopOnSizeError
        return errVals+['err02','','','','']

    for tipo,pattern in patterns:
        if pattern>'':
            match = re.search(pattern, fullText)
            if match:
                data_comprovante = extract_br_date(
                  match.group(1).strip() if match else None
                )
                emissor = extract_patterns(emissorPatterns,fullText,True)
                e = emissor[0] if emissor[0]>'' else 'generico'
                baseVals = [str(id), tipo, e, file.name, sha1sum, file_date_create]
                if tipo=="Pix":
                    baseVals.append(data_comprovante)
                    vals = extract_patterns(pixPatterns[e],fullText)
                    linha = baseVals + ['ok-auto'] + vals
                elif tipo=="Pagamento":
                    baseVals.append(data_comprovante)
                    # vals = ['','','']
                    vals = extract_patterns(pixPatterns[e],fullText)
                    linha = baseVals + ['ok-auto'] + vals
                else:
                    linha = baseVals + ['', 'err03','','','']
                return linha
    print("---- TEXTO SEM PADRAO RECONHECIDO! ----", file=sys.stderr)
    print(fullText, file=sys.stderr)
    globStop = stopOnNoPattern
    return errVals+['err04','','','','']

qt =1
pdf_files = list(folder_path.glob("*.pdf"))

print (csv_header)
for file in pdf_files:
    if file.name not in stopFiles:
        print( outputCSV_SEP.join( getPixPdf(file,qt) ) )
        qt = qt+1
        if globStop:
            print(" -- FIM --", file=sys.stderr)
            break
