import streamlit as st
import pandas as pd

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="HYLA - Gestión de Bases", layout="wide")

st.title("📂 Sistema de Distribución de Bases HYLA")
st.markdown("Selecciona uno o varios agentes para generar el archivo de contactos.")

# 1. ENLACE DE DATOS (REEMPLAZA ESTE LINK)
URL = 'https://docs.google.com/spreadsheets/d/139Q93zp478sAcLbW4xOVPAkI3VmYFbdLyCPphNngJFA/edit?gid=78532993#gid=78532993'
URL_EXPORT = URL.split('/edit')[0] + '/export?format=xlsx'

@st.cache_data(ttl=300)
def cargar_datos():
    # Carga el Excel desde Google Sheets
    df = pd.read_excel(URL_EXPORT)
    # Crea la columna de dueño real (Cedida a > Vendedor)
    df['Agente_Final'] = df['Cedida a'].fillna(df['Vendedor']).astype(str).str.strip()
    return df

try:
    df_raw = cargar_datos()

    # 2. FILTRADO ESTRATÉGICO
    estados = ['Demo', 'Demo online', 'demo recuperada', 'venta', 'venta online', 'venta recuperada']
    df_filtrado = df_raw[df_raw['Resultado Demo'].str.contains('|'.join(estados), case=False, na=False)].copy()

    # 3. NORMALIZACIÓN DE CONTACTOS
    def procesar_contacto(fila):
        nombre = str(fila['Referido']).strip()
        # Limpiar teléfono y asegurar 9 dígitos finales
        tel_limpio = "".join(filter(str.isdigit, str(fila['Telefono'])))
        num_final = tel_limpio[-9:]
        
        # Prefijo según resultado
        es_venta = 'venta' in str(fila['Resultado Demo']).lower()
        prefijo = "VENTA HYLA" if es_venta else "DEMO HYLA"
        
        return pd.Series([f"{prefijo} {nombre}", f"+56{num_final}"])

    df_filtrado[['Name', 'Mobile Phone']] = df_filtrado.apply(procesar_contacto, axis=1)

    # 4. ELIMINAR DUPLICADOS (Prioridad Venta)
    df_filtrado['Prioridad'] = df_filtrado['Resultado Demo'].str.contains('venta', case=False).astype(int)
    df_filtrado = df_filtrado.sort_values(by=['Mobile Phone', 'Prioridad'], ascending=[True, False])
    df_final = df_filtrado.drop_duplicates(subset='Mobile Phone', keep='first')

    # 5. INTERFAZ DE SELECCIÓN MÚLTIPLE
    lista_agentes = sorted([a for a in df_final['Agente_Final'].unique() if a not in ['nan', 'None', '']])
    
    seleccionados = st.multiselect("🔍 Busca y selecciona los agentes:", lista_agentes)

    if seleccionados:
        # Filtrar por los agentes elegidos
        base_descarga = df_final[df_final['Agente_Final'].isin(seleccionados)][['Name', 'Mobile Phone']]
        
        st.success(f"Se han consolidado {len(base_descarga)} contactos únicos.")
        
        # Generar CSV
        csv_data = base_descarga.to_csv(index=False, encoding='utf-8-sig')
        
        st.download_button(
            label=f"⬇️ Descargar Base para {len(seleccionados)} Agentes",
            data=csv_data,
            file_name="Base_Consolidada_Hyla.csv",
            mime='text/csv'
        )
    else:
        st.info("Por favor, selecciona al menos un nombre para habilitar la descarga.")

except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.warning("Verifica que el enlace sea correcto y tenga acceso público.")