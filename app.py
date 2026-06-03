import streamlit as st
import json
from google import genai
from google.genai import types

# Nastavení stránky Streamlit
st.set_page_config(
    page_title="AI Mentor - Hodnocení studentů",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


prompt = """
Analyzuj následující text studenta a vytvoř zpětnou vazbu zaměřenou výhradně na formální nedostatky.

Požadavky na zpětnou vazbu:

* Používej věcný, profesionální a neutrální tón.
* Nehodnoť studenta ani jeho schopnosti, zaměř se pouze na text.
* Nevkládej ironické, zlehčující, mentorující ani hovorové formulace.
* Nepoužívej obraty typu „tady narážíme na“, „učitelské fajnšmekerství“, „sice funguje, ale“, „správně by bylo“ bez vysvětlení apod.
* Formát Markdown, matematika pomocí LaTeXu.
* Jazyk čeština nebo slovenština.

Každou chybu popiš konkrétně:
* uveď, kde se vyskytuje,
* vysvětli, v čem spočívá,
* zdůvodni, proč je daný zápis nebo řešení z formálního hlediska nevhodné nebo nesprávné,
* uveď doporučení pro opravu.

Pokud je to vhodné, přidej příklad správného zápisu.

Piš tak, aby zpětná vazba sloužila jako seznam konkrétních úprav před odevzdáním opravené verze.

Zaměř se pouze na skutečné formální nedostatky (matematický zápis, notace, struktura řešení, označování veličin, jednotky, odkazy na obrázky/tabulky, typografická pravidla, pravopis apod.).

Nevytvářej chyby, které v textu nejsou.

Pokud je některá část pouze doporučením, nikoliv chybou, označ ji jako „Doporučení“.

Výstup strukturovaně rozděl do jednotlivých bodů.

Musíš se striktně zaměřit na adresnost: v sekci 'oblasti_ke_zlepseni' vždy cituj přesný kus textu/kódu ('kontext_textu') z dokumentu, kterého se kritika týká, aby student přesně věděl, kde udělal chybu. Hodnoť gramatiku, věcnou správnost, strukturu argumentace, čistotu kódu (pokud je přítomen) a dodržování formátu. 

Na závěr přidej stručné shrnutí:

Shrnutí k přepracování
* bod 1
* bod 2
* bod 3

"""

# Pomocná funkce pro konverzi .ipynb do čistého Markdownu
def convert_ipynb_to_md(file_content):
    try:
        notebook = json.loads(file_content)
        md_lines = []
        
        # Kontrola základní struktury notebooku
        if 'cells' not in notebook:
            return "Chyba: Neplatný formát Jupyter Notebooku."
            
        for i, cell in enumerate(notebook.get('cells', [])):
            cell_type = cell.get('cell_type')
            source = "".join(cell.get('source', []))
            
            if cell_type == 'markdown':
                md_lines.append(source + "\n")
            elif cell_type == 'code':
                md_lines.append(f"\n### [Buňka {i+1}] Zdrojový kód\n```python\n{source}\n```\n")
                
                # Zpracování výstupů z buňky (pokud existují)
                outputs = cell.get('outputs', [])
                for out in outputs:
                    if out.get('output_type') == 'stream' and 'text' in out:
                        text = "".join(out.get('text', []))
                        md_lines.append(f"*Výstup spuštění:*\n```text\n{text}\n```\n")
                    elif out.get('output_type') in ['execute_result', 'display_data'] and 'data' in out:
                        data = out.get('data', {})
                        if 'text/plain' in data:
                            text = "".join(data['text/plain'])
                            md_lines.append(f"*Výstup spuštění:*\n```text\n{text}\n```\n")
        return "\n".join(md_lines)
    except Exception as e:
        return f"Chyba při konverzi Jupyter Notebooku: {str(e)}"

# Hlavní UI aplikace
st.title("🎓 Profesionální AI Mentor")
st.subheader("Detailní zpětná vazba pro studentské práce (Markdown & Jupyter Notebooks)")
st.markdown(
    "Nahrajte svou práci ve formátu **Markdown (.md)** nebo **Jupyter Notebook (.ipynb)**. "
    "Pokročilý model AI provede hloubkovou analýzu, ohodnotí vaši práci a poskytne adresnou zpětnou vazbu vázanou přímo na váš text."
)

# Postranní panel (Sidebar) pro konfiguraci
st.sidebar.header("⚙️ Nastavení a API")
api_key_input = st.sidebar.text_input("Zadejte Google Gemini API Klíč:", type="password", help="Klíč získáte zdarma v Google AI Studio.")
model_choice = st.sidebar.selectbox("Zvolte model:", ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"], index=0, help="Flash je extrémně rychlý, Pro je vhodný pro hlubší logickou analýzu.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 Jak aplikace funguje:")
st.sidebar.write("1. Nahrajete soubor s úkolem.")
st.sidebar.write("2. Jupyter zápisníky se automaticky transformují na strukturovaný text.")
st.sidebar.write("3. AI zanalyzuje gramatiku, logiku, styl i kvalitu kódu.")
st.sidebar.write("4. Získáte interaktivní přehled s konkrétními návrhy na opravu.")

# Výběr souboru
uploaded_file = st.file_uploader("Vyberte soubor k analýze", type=["md", "ipynb"])

if uploaded_file is not None:
    file_name = uploaded_file.name
    file_bytes = uploaded_file.read()
    
    # Detekce typu a zpracování obsahu
    if file_name.endswith('.ipynb'):
        st.info("🔄 Detekován Jupyter Notebook. Převádím obsah na formát Markdown...")
        raw_content = file_bytes.decode("utf-8", errors="ignore")
        markdown_content = convert_ipynb_to_md(raw_content)
    else:
        st.info("📄 Detekován Markdown soubor. Načítám text...")
        markdown_content = file_bytes.decode("utf-8", errors="ignore")
        
    # Náhled dokumentu
    with st.expander("👁️ Zobrazit náhled převedeného/načteného dokumentu"):
        st.markdown(markdown_content if markdown_content.strip() else "*Dokument je prázdný.*")

    # Tlačítko pro spuštění analýzy
    st.markdown("### 🚀 Spuštění evaluace")
    if st.button("Analyzovat práci studenta", type="primary"):
        if not api_key_input:
            st.error("❌ Prosím, zadejte platný Gemini API klíč v levém panelu, abyste mohli spustit analýzu.")
        elif not markdown_content.strip():
            st.error("❌ Dokument neobsahuje žádný text k analýze.")
        else:
            with st.spinner("⏳ AI Mentor podrobně studuje dokument a připravuje hodnocení..."):
                try:
                    # Inicializace Google GenAI klienta
                    client = genai.Client(api_key=api_key_input)
                    
                    # Definice strukturovaného schématu odpovědi pro přehledné zobrazení v UI
                    response_schema = {
                        "type": "OBJECT",
                        "properties": {
                            "celkove_hodnoceni": {"type": "STRING"},
                            "skore": {"type": "INTEGER"},
                            "silne_stranky": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "oblasti_ke_zlepseni": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "kontext_textu": {"type": "STRING"},
                                        "vysvetleni_chyby": {"type": "STRING"},
                                        "navrh_opravy": {"type": "STRING"}
                                    },
                                    "required": ["kontext_textu", "vysvetleni_chyby", "navrh_opravy"]
                                }
                            },
                            "technicka_a_stylisticka_recenze": {"type": "STRING"}
                        },
                        "required": ["celkove_hodnoceni", "skore", "silne_stranky", "oblasti_ke_zlepseni", "technicka_a_stylisticka_recenze"]
                    }
                    
                    # Systémové instrukce pro mentora
                    system_instruction = prompt
                    
                    # Volání Gemini API
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.2, # Nižší kreativita pro přesnější hodnocení
                    )
                    
                    response = client.models.generate_content(
                        model=model_choice,
                        contents=f"Zde je studentská práce k vyhodnocení:\n\n{markdown_content}",
                        config=config
                    )
                    
                    # Parsování výsledku
                    vysledek = json.loads(response.text)
                    
                    st.success("✅ Analýza byla úspěšně dokončena!")
                    st.markdown("---")
                    
                    # 1. HLAVNÍ METRIKY A SHRNUTÍ
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        skore = vysledek.get("skore", 0)
                        if skore >= 80:
                            st.metric(label="Celkové hodnocení", value=f"{skore} / 100", delta="Výborně")
                        elif skore >= 50:
                            st.metric(label="Celkové hodnocení", value=f"{skore} / 100", delta="Průměr", delta_color="off")
                        else:
                            st.metric(label="Celkové hodnocení", value=f"{skore} / 100", delta="Vyžaduje opravu", delta_color="inverse")
                    
                    with col2:
                        st.markdown("### 📋 Shrnutí mentora")
                        st.write(vysledek.get("celkove_hodnoceni", ""))
                        
                    st.markdown("---")
                    
                    # 2. DETAILNÍ VÝSLEDKY POMOCÍ TABS
                    tab1, tab2, tab3 = st.tabs(["🌟 Silné stránky", "🛠️ Adresné oblasti ke zlepšení", "💻 Technická & Stylistická recenze"])
                    
                    with tab1:
                        st.markdown("### Co se v práci povedlo:")
                        silne_stranky = vysledek.get("silne_stranky", [])
                        if silne_stranky:
                            for bod in silne_stranky:
                                st.markdown(f"• {bod}")
                        else:
                            st.write("*Žádné specifické silné stránky nebyly vyzdvihnuty.*")
                            
                    with tab2:
                        st.markdown("### Konkrétní nedostatky provázané s textem:")
                        st.caption("Níže naleznete přesné pasáže z vaší práce, které vyžadují úpravu, spolu s vysvětlením a doporučeným řešením.")
                        
                        oblasti = vysledek.get("oblasti_ke_zlepseni", [])
                        if oblasti:
                            for idx, oblast in enumerate(oblasti):
                                with st.container(border=True):
                                    st.markdown(f"**Chyba č. {idx + 1}**")
                                    # Ukázka problematického textu
                                    st.markdown(f"🔍 **Původní pasáž v dokumentu:**")
                                    st.info(f'"{oblast.get("kontext_textu", "")}"')
                                    
                                    # Problém a řešení
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        st.markdown("⚠️ **V čem je problém:**")
                                        st.write(oblast.get("vysvĕtleni_chyby", oblast.get("vysvetleni_chyby", "")))
                                    with col_b:
                                        st.markdown("💡 **Doporučený návrh opravy:**")
                                        st.write(oblast.get("navrh_opravy", ""))
                        else:
                            st.success("🎉 Skvělá práce! AI mentor nenašel žádné zásadní oblasti ke zlepšení.")
                            
                    with tab3:
                        st.markdown("### Hloubková technická a stylistická recenze")
                        st.write(vysledek.get("technicka_a_stylisticka_recenze", ""))
                        
                except Exception as e:
                    st.error(f"🔴 Došlo k chybě při komunikaci s Gemini API nebo zpracování odpovědi. Detaily: {str(e)}")
                    st.info("Ujistěte se, že máte správně nastavený API klíč a že balíček `google-genai` je správně nainstalován.")