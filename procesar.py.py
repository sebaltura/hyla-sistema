import pandas as pd
import os

URL = 'https://docs.google.com/spreadsheets/d/139Q93zp478sAcLbW4xOVPAkI3VmYFbdLyCPphNngJFA/edit?gid=78532993#gid=78532993'
URL_EXPORT = URL.split('/edit')[0] + '/export?format=xlsx'

CARPETA_SALIDA = 'Bases_Agentes'
if not os.path.exists(CARPETA_SALIDA): os.makedirs(CARPETA_SALIDA)

print("Procesando lista completa de agentes...")

df = pd.read_excel(URL_EXPORT)
df['Agente_Final'] = df['Cedida a'].fillna(df['Vendedor']).astype(str).str.strip()

# Filtro de estados
estados = ['Demo', 'Demo online', 'demo recuperada', 'venta', 'venta online', 'venta recuperada']
df = df[df['Resultado Demo'].str.contains('|'.join(estados), case=False, na=False)]

def limpiar(fila):
    nombre = str(fila['Referido']).strip()
    tel = str(fila['Telefono']).split('.')[0].replace(' ', '').replace('+', '')
    prefijo = "VENTA HYLA" if 'venta' in str(fila['Resultado Demo']).lower() else "DEMO HYLA"
    return pd.Series([f"{prefijo} {nombre}", f"+56{tel[-9:]}"])

df[['Nombre_Display', 'Telefono_Final']] = df.apply(limpiar, axis=1)

# Prioridad Venta sobre Demo
df['Es_Venta'] = df['Resultado Demo'].str.contains('venta', case=False).astype(int)
df = df.sort_values(by=['Telefono_Final', 'Es_Venta'], ascending=[True, False])
df = df.drop_duplicates(subset='Telefono_Final', keep='first')

# Generar TODOS los agentes
for agente, data in df.groupby('Agente_Final'):
    if agente not in ['nan', 'None', '']:
        # Limpiamos el nombre del archivo de caracteres extraños
        nombre_limpio = "".join([c for c in agente if c.isalnum() or c==' ']).replace(' ', '_')
        archivo = f"{CARPETA_SALIDA}/Base_{nombre_limpio}.csv"
        output = data.rename(columns={'Nombre_Display': 'Name', 'Telefono_Final': 'Mobile Phone'})
        output[['Name', 'Mobile Phone']].to_csv(archivo, index=False, encoding='utf-8-sig')

print(f"¡Hecho! Se generaron archivos para {len(df['Agente_Final'].unique())} agentes.")