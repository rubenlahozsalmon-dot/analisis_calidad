import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set page configuration
st.set_page_config(page_title="Dashboard de Logística", layout="wide")

# 1. App Header
st.title("🚚 Dashboard Automatizado de Entregas e Incidencias")
st.markdown("Sube un archivo Excel para procesar los datos y generar el análisis automáticamente.")

# 2. File Uploader
uploaded_file = st.file_uploader("Selecciona el archivo Excel (.xls)", type=["xls"])

if uploaded_file is not None:
    # 3. Data Processing Functionality
    try:
        # Load raw data
        df_raw = pd.read_excel(uploaded_file, header=None)

        # Identify Sections
        idx_entregas = df_raw[df_raw[0].astype(str).str.contains('ENTREGAS EFECTUADAS', na=False, case=True)].index
        idx_incidencias = df_raw[df_raw[0].astype(str).str.contains('INCIDENCIAS', na=False, case=True)].index

        # Assign 'Estado'
        df_raw['Estado'] = np.nan
        if not idx_entregas.empty:
            start_entregas = idx_entregas[0]
            end_entregas = idx_incidencias[0] if not idx_incidencias.empty else len(df_raw)
            df_raw.loc[start_entregas:end_entregas-1, 'Estado'] = 'Entregas Efectuadas'

        if not idx_incidencias.empty:
            start_incidencias = idx_incidencias[0]
            df_raw.loc[start_incidencias:, 'Estado'] = 'Incidencias'

        # Extract and Fill Repartidor
        df_raw['Repartidor'] = np.where(df_raw[4].astype(str).str.contains('CONDUCTOR', na=False), df_raw[5], np.nan)
        df_raw['Repartidor'] = df_raw['Repartidor'].str.replace(r'^.*:\s*\d*\s*', '', regex=True).str.strip()
        df_raw['Repartidor'] = df_raw['Repartidor'].ffill()

        # Clean and Format
        df_proc = df_raw.rename(columns={9: 'Fecha', 5: 'CP'})[['Fecha', 'CP', 'Repartidor', 'Estado']]
        df_proc['Fecha'] = pd.to_datetime(df_proc['Fecha'], errors='coerce')
        df_proc = df_proc.dropna(subset=['Fecha'])
        df_proc['CP'] = df_proc['CP'].astype(str).str.strip().str.replace('.0', '', regex=False)
        df_proc['Repartidor'] = df_proc['Repartidor'].fillna('SIN ASIGNAR').str.upper()
        df_proc['Estado'] = df_proc['Estado'].fillna('DESCONOCIDO')
        df_proc['Hora'] = df_proc['Fecha'].dt.hour
        df_proc['Dia'] = df_proc['Fecha'].dt.date

        # 4. Display Metrics
        total_entregas = len(df_proc[df_proc['Estado'] == 'Entregas Efectuadas'])
        total_incidencias = len(df_proc[df_proc['Estado'] == 'Incidencias'])

        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Registros", len(df_proc))
        m2.metric("Entregas Efectuadas", total_entregas)
        m3.metric("Incidencias", total_incidencias)

        # 5. Visualizations
        st.subheader("📊 Análisis de Datos")
        v_col1, v_col2 = st.columns(2)

        with v_col1:
            st.write("**Top 15 Códigos Postales con Incidencias**")
            df_inc = df_proc[df_proc['Estado'] == 'Incidencias']
            top_cp = df_inc['CP'].value_counts().head(15).reset_index()
            top_cp.columns = ['CP', 'Frecuencia']
            
            fig_cp, ax_cp = plt.subplots(figsize=(10, 6))
            sns.barplot(data=top_cp, x='CP', y='Frecuencia', hue='CP', palette='magma', legend=False, ax=ax_cp)
            plt.xticks(rotation=45)
            st.pyplot(fig_cp)

        with v_col2:
            st.write("**Evolución Temporal (Incidencias vs Entregas)**")
            trend = df_proc.pivot_table(index='Hora', columns='Estado', aggfunc='size', fill_value=0)
            
            fig_time, ax_time = plt.subplots(figsize=(10, 6))
            if 'Entregas Efectuadas' in trend.columns:
                ax_time.plot(trend.index, trend['Entregas Efectuadas'], marker='o', label='Entregas', color='green', linewidth=2)
            if 'Incidencias' in trend.columns:
                ax_time.plot(trend.index, trend['Incidencias'], marker='x', label='Incidencias', color='red', linewidth=2)
            ax_time.set_xlabel("Hora del Día")
            ax_time.set_ylabel("Cantidad")
            ax_time.legend()
            st.pyplot(fig_time)

        # 6. Quantitative Table
        st.subheader("📑 Resumen por Repartidor y CP")
        summary = df_proc.pivot_table(
            index=['Repartidor', 'CP', 'Dia'],
            columns='Estado',
            aggfunc='size',
            fill_value=0
        ).reset_index()
        
        # Ensure columns exist
        for col in ['Entregas Efectuadas', 'Incidencias']:
            if col not in summary.columns: summary[col] = 0
        
        summary['Total'] = summary['Entregas Efectuadas'] + summary['Incidencias']
        st.dataframe(summary, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Esperando carga de archivo...")
