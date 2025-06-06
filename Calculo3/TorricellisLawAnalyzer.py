import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import locale
def setLocale():
    if locale.getdefaultlocale()[0] == 'pt_BR':
        st.set_page_config(layout="wide",page_title="Analisador da Lei de Torricelli")
    else:
        st.set_page_config(layout="wide",page_title="Torricelli's Law Analyzer")

def loadFromInside():
    timeInSeconds = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 123]

    heightInCentimeters = [22.25, 21.0, 20.0, 18.8, 17.75, 16.85, 15.9, 15.0, 14.1, 13.15, 12.5, 11.6, 11.0, 10.125, 9.75, 9.0, 8.4, 7.6, 7.1, 6.85, 6.4, 6.0, 5.55, 5.4, 5.1, 5.0]
    
    if not locale.getdefaultlocale()[0] == 'pt_BR':
        dfInside = pd.DataFrame(list(zip(timeInSeconds, heightInCentimeters)), columns=['Time (s)', 'Height (cm)'])
    else:
        dfInside = pd.DataFrame(list(zip(timeInSeconds, heightInCentimeters)), columns=['Tempo (s)','Altura (cm)']) 
    return dfInside

# --- 1. TorricelliCalculator (Python adaptation) ---
def calculate_theoretical_height(h0, t, A_tank, A_hole, g):
    """
    Calculates the theoretical height of water in a cylindrical tank at a given time
    based on Torricelli's Law.
    Formula: h(t) = (sqrt(h0) - (A_hole / A_tank) * sqrt(g/2) * t)^2

    Args:
        h0 (float): Initial height of the water (cm).
        t (float or np.array): Time elapsed (s). Can be a single value or a NumPy array.
        A_tank (float): Area of the cylinder base (cm^2).
        A_hole (float): Area of the hole (cm^2).
        g (float): Acceleration due to gravity (cm/s^2).

    Returns:
        float or np.array: Theoretical height at time t (cm). Clamps at 0 if height would be negative.
    """
    if h0 < 0 or A_tank <= 0 or A_hole <= 0 or g <= 0:
        # Handle invalid constant inputs gracefully
        return np.zeros_like(t) if isinstance(t, np.ndarray) else 0.0

    # Ensure t is a NumPy array for element-wise operations if it's not already
    t_array = np.atleast_1d(t)

    term1 = np.sqrt(h0)
    term2 = (A_hole / A_tank) * np.sqrt(g / 2.0) * t_array

    result = term1 - term2

    # Height cannot be negative, so clamp it at 0
    theoretical_heights = np.maximum(0.0, result)**2

    return theoretical_heights if isinstance(t, np.ndarray) else theoretical_heights[0]





# --- 2. Streamlit Application ---
def setLanguageApp(Value):
    if Value == "Português Brasileiro/Brazilian Portuguese":
        portuguese_program()
    else:
        english_program()
    

def english_program():
    st.title("1st Degree EDO's in everyday life")
    st.write("""Activity Calculus III 2025-1
            
    PUC Minas Coração Eucaristico 

    Student: Gabriel da Silva Cassino

    Data Analyzer by Torricelli's Law""")


    # --- Sidebar for Inputs ---
    st.sidebar.header("Parameters & Options")

    uploaded_file = st.sidebar.file_uploader("Upload CSV Data (Time,Height)", type=["csv"])

    inside_program=st.sidebar.button("Load Default Data")

    cylinder_radius = st.sidebar.number_input(
        "Cylinder Radius (cm):",
        min_value=0.1,
        value=5.0,
        step=0.1,
        format="%.1f"
    )

    hole_radius = st.sidebar.number_input(
        "Hole Radius (cm):",
        min_value=0.01,
        value=0.25,
        step=0.01,
        format="%.2f"
    )

    plot_option = st.sidebar.radio(
        "Select Plot Option:",
        ("Show Scatter Plot Only", "Compare with Torricelli's Law")
    )

    # --- Main Content Area ---
    st.header("Analysis Results")

    if uploaded_file is not None:
        try:
            # Read CSV data
            # Assuming first column is time, second is height. No header by default.
            # For robustness, consider adding header=None and then renaming columns
            df = pd.read_csv(uploaded_file, header=None, names=['Time (s)', 'Height (cm)'])

            # Basic validation for columns
            if 'Time (s)' not in df.columns or 'Height (cm)' not in df.columns:
                st.error("CSV must contain 'Time (s)' and 'Height (cm)' columns.")
                st.stop() # Stop execution if columns are missing

            # Ensure numeric types
            df['Time (s)'] = pd.to_numeric(df['Time (s)'], errors='coerce')
            df['Height (cm)'] = pd.to_numeric(df['Height (cm)'], errors='coerce')
            df.dropna(inplace=True) # Drop rows with non-numeric values

            if df.empty:
                st.warning("No valid numeric data found in the CSV after parsing.")
                st.stop()

            # Display raw data (optional, for verification)
            st.subheader("Raw Experimental Data Preview")
            st.dataframe(df.head())

            # Validate radii inputs
            if cylinder_radius <= 0 or hole_radius <= 0:
                st.error("Cylinder and Hole radii must be positive.")
                st.stop()
            if hole_radius >= cylinder_radius:
                st.error("Hole radius must be smaller than cylinder radius.")
                st.stop()

            # --- Plotting ---
            fig, ax = plt.subplots(figsize=(10, 6))

            # Plot experimental data
            ax.scatter(df['Time (s)'], df['Height (cm)'], label='Experimental Data', color='blue', s=20)

            # Add a simple trend line (e.g., linear regression for general trend)
            # For a more physically accurate trend, you might fit to the Torricelli's law form
            z = np.polyfit(df['Time (s)'], df['Height (cm)'], 2) # Example: 2nd degree polynomial
            p = np.poly1d(z)
            ax.plot(df['Time (s)'], p(df['Time (s)']), color='red', linestyle='--', label='Polynomial Trend')

            if plot_option == "Compare with Torricelli's Law":
                st.subheader("Torricelli's Law Comparison")
                
                # Constants
                GRAVITY_CM_PER_SEC_SQ = 981.0 # Acceleration due to gravity in cm/s^2
                
                # Get initial height from experimental data
                initial_height = df['Height (cm)'].iloc[0]
                
                # Calculate areas
                A_tank = np.pi * (cylinder_radius ** 2)
                A_hole = np.pi * (hole_radius ** 2)

                st.write(f"Initial Height (h0): **{initial_height:.2f} cm**")
                st.write(f"Cylinder Area (A_tank): **{A_tank:.2f} cm²**")
                st.write(f"Hole Area (A_hole): **{A_hole:.2f} cm²**")
                st.write(f"Gravity (g): **{GRAVITY_CM_PER_SEC_SQ:.2f} cm/s²**")

                # Calculate theoretical heights for the same time points as experimental data
                theoretical_heights = calculate_theoretical_height(
                    initial_height,
                    df['Time (s)'].values, # Pass as NumPy array for vectorized calculation
                    A_tank,
                    A_hole,
                    GRAVITY_CM_PER_SEC_SQ
                )
                
                # Plot theoretical data
                ax.plot(df['Time (s)'], theoretical_heights, label="Torricelli's Law (Theoretical)", color='green', linestyle='-')

            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Height (cm)")
            ax.set_title("Water Height vs. Time")
            ax.legend()
            ax.grid(True)

            st.pyplot(fig) # Display the plot in Streamlit

        except Exception as e:
            st.error(f"An error occurred: {e}. Please check your CSV file format and inputs.")
            st.exception(e) # Display full traceback for debugging
    elif inside_program:
        try:
            # Assigns the Pandas Dataframe the values ​​predefined by the function
            df = loadFromInside()

            # Display raw data (optional, for verification)
            st.subheader("Raw Experimental Data Preview")
            st.dataframe(df.head())

            # Validate radii inputs
            if cylinder_radius <= 0 or hole_radius <= 0:
                st.error("Cylinder and Hole radii must be positive.")
                st.stop()
            if hole_radius >= cylinder_radius:
                st.error("Hole radius must be smaller than cylinder radius.")
                st.stop()

            # --- Plotting ---
            fig, ax = plt.subplots(figsize=(10, 6))

            # Plot experimental data
            ax.scatter(df['Time (s)'], df['Height (cm)'], label='Experimental Data', color='blue', s=20)

            # Add a simple trend line (e.g., linear regression for general trend)
            # For a more physically accurate trend, you might fit to the Torricelli's law form
            z = np.polyfit(df['Time (s)'], df['Height (cm)'], 2) # Example: 2nd degree polynomial
            p = np.poly1d(z)
            ax.plot(df['Time (s)'], p(df['Time (s)']), color='red', linestyle='--', label='Polynomial Trend')

            if plot_option == "Compare with Torricelli's Law":
                st.subheader("Torricelli's Law Comparison")
                
                # Constants
                GRAVITY_CM_PER_SEC_SQ = 981.0 # Acceleration due to gravity in cm/s^2
                
                # Get initial height from experimental data
                initial_height = df['Height (cm)'].iloc[0]
                
                # Calculate areas
                A_tank = np.pi * (cylinder_radius ** 2)
                A_hole = np.pi * (hole_radius ** 2)

                st.write(f"Initial Height (h0): **{initial_height:.2f} cm**")
                st.write(f"Cylinder Area (A_tank): **{A_tank:.2f} cm²**")
                st.write(f"Hole Area (A_hole): **{A_hole:.2f} cm²**")
                st.write(f"Gravity (g): **{GRAVITY_CM_PER_SEC_SQ:.2f} cm/s²**")

                # Calculate theoretical heights for the same time points as experimental data
                theoretical_heights = calculate_theoretical_height(
                    initial_height,
                    df['Time (s)'].values, # Pass as NumPy array for vectorized calculation
                    A_tank,
                    A_hole,
                    GRAVITY_CM_PER_SEC_SQ
                )
                
                # Plot theoretical data
                ax.plot(df['Time (s)'], theoretical_heights, label="Torricelli's Law (Theoretical)", color='green', linestyle='-')

            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Height (cm)")
            ax.set_title("Water Height vs. Time")
            ax.legend()
            ax.grid(True)

            st.pyplot(fig) # Display the plot in Streamlit

        except Exception as e:
            st.error(f"An error occurred: {e}. Please check your CSV file format and inputs.")
            st.exception(e) # Display full traceback for debugging

    else:
        st.info("Please upload a CSV file to get started. The CSV should have time in the first column and height in the second column (no header).")
        st.markdown("""
        **Example CSV Format:**
        ```
        0.0,20.0
        1.0,19.5
        2.0,18.8
        3.0,18.0
        4.0,17.1
        5.0,16.0
        ```
        """)

def portuguese_program():
    st.title("EDO's de 1º Grau no cotidiano")
    st.write("""Atividade Calculo III 2025-1
            
    PUC Minas Coração Eucaristico 

    Aluno: Gabriel da Silva Cassino

    Analisador de Dados pela Lei de Torricelli""")

    # --- Barra Lateral para Entradas ---
    st.sidebar.header("Parâmetros e Opções")

    uploaded_file = st.sidebar.file_uploader("Carregar Dados CSV (Tempo,Altura)", type=["csv"])

    inside_program=st.sidebar.button("Carregar Dados predefinidos")

    cylinder_radius = st.sidebar.number_input(
        "Raio do Cilindro (cm):",
        min_value=0.1,
        value=5.0,
        step=0.1,
        format="%.1f"
    )

    hole_radius = st.sidebar.number_input(
        "Raio do Furo (cm):",
        min_value=0.01,
        value=0.25,
        step=0.01,
        format="%.2f"
    )

    plot_option = st.sidebar.radio(
        "Selecionar Opção de Gráfico:",
        ("Mostrar Apenas Gráfico de Dispersão", "Comparar com a Lei de Torricelli")
    )

    # --- Área de Conteúdo Principal ---
    st.header("Resultados da Análise")

    if uploaded_file is not None:
        try:
            # Ler dados CSV
            # Assumindo que a primeira coluna é tempo, a segunda é altura. Sem cabeçalho por padrão.
            # Para maior robustez, considere adicionar header=None e depois renomear as colunas
            df = pd.read_csv(uploaded_file, header=None, names=['Tempo (s)', 'Altura (cm)'])

            # Validação básica para colunas
            if 'Tempo (s)' not in df.columns or 'Altura (cm)' not in df.columns:
                st.error("O CSV deve conter as colunas 'Tempo (s)' e 'Altura (cm)'.")
                st.stop() # Para a execução se as colunas estiverem faltando

            # Garante tipos numéricos
            df['Tempo (s)'] = pd.to_numeric(df['Tempo (s)'], errors='coerce')
            df['Altura (cm)'] = pd.to_numeric(df['Altura (cm)'], errors='coerce')
            df.dropna(inplace=True) # Remove linhas com valores não numéricos

            if df.empty:
                st.warning("Nenhum dado numérico válido encontrado no CSV após a análise.")
                st.stop()

            # Exibe dados brutos (opcional, para verificação)
            st.subheader("Prévia dos Dados Experimentais Brutos")
            st.dataframe(df.head())

            # Valida entradas de raios
            if cylinder_radius <= 0 or hole_radius <= 0:
                st.error("Os raios do Cilindro e do Furo devem ser positivos.")
                st.stop()
            if hole_radius >= cylinder_radius:
                st.error("O raio do furo deve ser menor que o raio do cilindro.")
                st.stop()

            # --- Plotagem ---
            fig, ax = plt.subplots(figsize=(10, 6))

            # Plota dados experimentais
            ax.scatter(df['Tempo (s)'], df['Altura (cm)'], label='Dados Experimentais', color='blue', s=20)

            # Adiciona uma linha de tendência simples (ex: regressão polinomial para tendência geral)
            # Para uma tendência fisicamente mais precisa, você pode ajustar à forma da lei de Torricelli
            z = np.polyfit(df['Tempo (s)'], df['Altura (cm)'], 2) # Exemplo: polinômio de 2º grau
            p = np.poly1d(z)
            ax.plot(df['Tempo (s)'], p(df['Tempo (s)']), color='red', linestyle='--', label='Tendência Polinomial')

            if plot_option == "Comparar com a Lei de Torricelli":
                st.subheader("Comparação com a Lei de Torricelli")
                
                # Constantes
                GRAVITY_CM_PER_SEC_SQ = 981.0 # Aceleração devido à gravidade em cm/s^2
                
                # Obtém a altura inicial dos dados experimentais
                initial_height = df['Altura (cm)'].iloc[0]
                
                # Calcula as áreas
                A_tanque = np.pi * (cylinder_radius ** 2)
                A_furo = np.pi * (hole_radius ** 2)

                st.write(f"Altura Inicial (h0): **{initial_height:.2f} cm**")
                st.write(f"Área do Cilindro (A_tanque): **{A_tanque:.2f} cm²**")
                st.write(f"Área do Furo (A_furo): **{A_furo:.2f} cm²**")
                st.write(f"Gravidade (g): **{GRAVITY_CM_PER_SEC_SQ:.2f} cm/s²**")

                # Calcula as alturas teóricas para os mesmos pontos de tempo dos dados experimentais
                theoretical_heights = calculate_theoretical_height(
                    initial_height,
                    df['Tempo (s)'].values, # Passa como array NumPy para cálculo vetorizado
                    A_tanque,
                    A_furo,
                    GRAVITY_CM_PER_SEC_SQ
                )
                
                # Plota dados teóricos
                ax.plot(df['Tempo (s)'], theoretical_heights, label="Lei de Torricelli (Teórica)", color='green', linestyle='-')

            ax.set_xlabel("Tempo (s)")
            ax.set_ylabel("Altura (cm)")
            ax.set_title("Altura da Água vs. Tempo")
            ax.legend()
            ax.grid(True)

            st.pyplot(fig) # Exibe o gráfico no Streamlit

        except Exception as e:
            st.error(f"Ocorreu um erro: {e}. Por favor, verifique o formato do seu arquivo CSV e as entradas.")
            st.exception(e) # Exibe o rastreamento completo para depuração
    elif inside_program:
        try:
            # Carrega no Pandas Dataframe os valores ​​predefinidos pela função
            df = loadFromInside()
            # Exibe dados brutos (opcional, para verificação)
            st.subheader("Prévia dos Dados Experimentais Brutos")
            st.dataframe(df.head())

            # Valida entradas de raios
            if cylinder_radius <= 0 or hole_radius <= 0:
                st.error("Os raios do Cilindro e do Furo devem ser positivos.")
                st.stop()
            if hole_radius >= cylinder_radius:
                st.error("O raio do furo deve ser menor que o raio do cilindro.")
                st.stop()

            # --- Plotagem ---
            fig, ax = plt.subplots(figsize=(10, 6))

            # Plota dados experimentais
            ax.scatter(df['Tempo (s)'], df['Altura (cm)'], label='Dados Experimentais', color='blue', s=20)

            # Adiciona uma linha de tendência simples (ex: regressão polinomial para tendência geral)
            # Para uma tendência fisicamente mais precisa, você pode ajustar à forma da lei de Torricelli
            z = np.polyfit(df['Tempo (s)'], df['Altura (cm)'], 2) # Exemplo: polinômio de 2º grau
            p = np.poly1d(z)
            ax.plot(df['Tempo (s)'], p(df['Tempo (s)']), color='red', linestyle='--', label='Tendência Polinomial')

            if plot_option == "Comparar com a Lei de Torricelli":
                st.subheader("Comparação com a Lei de Torricelli")
                
                # Constantes
                GRAVITY_CM_PER_SEC_SQ = 981.0 # Aceleração devido à gravidade em cm/s^2
                
                # Obtém a altura inicial dos dados experimentais
                initial_height = df['Altura (cm)'].iloc[0]
                
                # Calcula as áreas
                A_tanque = np.pi * (cylinder_radius ** 2)
                A_furo = np.pi * (hole_radius ** 2)

                st.write(f"Altura Inicial (h0): **{initial_height:.2f} cm**")
                st.write(f"Área do Cilindro (A_tanque): **{A_tanque:.2f} cm²**")
                st.write(f"Área do Furo (A_furo): **{A_furo:.2f} cm²**")
                st.write(f"Gravidade (g): **{GRAVITY_CM_PER_SEC_SQ:.2f} cm/s²**")

                # Calcula as alturas teóricas para os mesmos pontos de tempo dos dados experimentais
                theoretical_heights = calculate_theoretical_height(
                    initial_height,
                    df['Tempo (s)'].values, # Passa como array NumPy para cálculo vetorizado
                    A_tanque,
                    A_furo,
                    GRAVITY_CM_PER_SEC_SQ
                )
                
                # Plota dados teóricos
                ax.plot(df['Tempo (s)'], theoretical_heights, label="Lei de Torricelli (Teórica)", color='green', linestyle='-')

            ax.set_xlabel("Tempo (s)")
            ax.set_ylabel("Altura (cm)")
            ax.set_title("Altura da Água vs. Tempo")
            ax.legend()
            ax.grid(True)

            st.pyplot(fig) # Exibe o gráfico no Streamlit

        except Exception as e:
            st.error(f"Ocorreu um erro: {e}. Por favor, verifique o formato do seu arquivo CSV e as entradas.")
            st.exception(e) # Exibe o rastreamento completo para depuração
    else:
        st.info("Por favor, carregue um arquivo CSV para começar. O CSV deve ter o tempo na primeira coluna e a altura na segunda coluna (sem cabeçalho).")
        st.markdown("""
        **Exemplo de Formato CSV:**
        ```
        0.0,20.0
        1.0,19.5
        2.0,18.8
        3.0,18.0
        4.0,17.1
        5.0,16.0
        ```
        """)
# PT_BR: Define título da página com base no idioma do sistema operacional
# EN_US: Set page title based on operating system language
setLocale() 

# PT_BR: Define o idioma com base na escolha do usuario
# EN_US: Set language based on user choice
optlanguage=st.selectbox("Language Program/Idioma do Programa",["Please choose a language/Escolha um idioma por favor","Português Brasileiro/Brazilian Portuguese","English-US/Inglês-EUA"])
if not optlanguage=="Please choose a language/Escolha um idioma por favor":
    setLanguageApp(optlanguage)
else:
    st.write("""
EN-US: Waiting language choice ....
             
PT-BR: Aguardando Escolha de Idioma ....
""")