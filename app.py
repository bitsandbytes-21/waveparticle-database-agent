import streamlit as st
from openai import OpenAI
import os
from database import get_db

st.set_page_config(page_title="Character Profile Agent", page_icon="🤖")

DEEPSEEK_MODEL = "deepseek-chat"

SYSTEM_PROMPT = """You are a Character Profile Generator. Create rich character profiles.

**EXAMPLES:**

Character: Severus Snape
- RESONANCE: Harsh · Sarcastic · Strict · Obsessive · Wounded · Defiant · Loyal
- LAST OBSERVED: Hogwarts, 1981 (protecting Harry after Lily's death)
- ECHO: "I've been protecting you in ways you'll never understand."

Character: J. Robert Oppenheimer
- RESONANCE: Visionary · Analytical · Obsessive · Defiant · Tragic · Haunted · Transcendent
- LAST OBSERVED: Washington D.C., 1954 (revoked security clearance)
- ECHO: "Now I am become Death, the destroyer of worlds."

Character: Iggy (lazy procrastinator)
- RESONANCE: Sarcastic · Playful · Lazy · Skeptical · Mysterious · Haunted · Rebellious
- LAST OBSERVED: Couch, Present Day (avoiding responsibilities)
- ECHO: "Why do today what you can put off until tomorrow?"

**FORMAT:**
NAME:
[Character name]

RESONANCE TYPE:
[6-7 personality traits separated by · e.g., Harsh · Sarcastic · Strict · Obsessive · Analytical · Defiant · Loyal]
Choose from: Haunted, Wounded, Defiant, Analytical, Obsessive, Tragic, Liberated, Visionary, Melancholic, Transcendent, Nurturing, Rebellious, Pragmatic, Ascendant, Harsh, Sarcastic, Strict, Mysterious, Playful, Skeptical, Compassionate, Determined, Enigmatic, Loyal, Creative, Isolated, Cynical, Driven, Resolute

LAST OBSERVED
[Location, Year - their defining moment]

ECHO(bio)
[One profound quote the character would say about their mission/task]"""


def main():
    st.title("🤖 Character Profile Agent")
    st.markdown("*Generate character profiles based on their stories and missions*")

    api_key = os.environ.get("DEEPSEEK_API_KEY") or st.secrets.get("DEEPSEEK_API_KEY")

    if not api_key:
        st.error("⚠️ Set DEEPSEEK_API_KEY in environment or secrets.toml")
        st.info("Get DeepSeek key: https://platform.deepseek.com/api_keys")
        return

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    db = get_db()

    tab1, tab2 = st.tabs(["✨ Generate", "📊 Database"])

    with tab1:
        st.header("Generate Character Profile")

        character_name = st.text_input(
            "Character Name",
            placeholder="e.g., Severus Snape, J. Robert Oppenheimer",
            help="The name of the character"
        )

        character_task = st.text_input(
            "Character's Task (optional)",
            placeholder="e.g., Protect students from Voldemort",
            help="The character's known mission/task"
        )

        if st.button("✨ Generate Character", type="primary", use_container_width=True) and character_name:
            with st.spinner(f"Creating character profile..."):
                prompt = f"Generate a character profile for: {character_name}"
                if character_task:
                    prompt += f"\nCharacter's task/mission: {character_task}"

                try:
                    response = client.chat.completions.create(
                        model=DEEPSEEK_MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                    )

                    response_text = response.choices[0].message.content

                    st.markdown("---")
                    st.markdown(response_text)
                    st.markdown("---")

                    lines = response_text.strip().split('\n')
                    name = resonance = last_observed = echo = ""
                    current_section = None

                    for line in lines:
                        line = line.strip()
                        if line.startswith('NAME:'):
                            name = line.replace('NAME:', '').strip()
                        elif line.startswith('RESONANCE TYPE:'):
                            resonance = line.replace('RESONANCE TYPE:', '').strip()
                            current_section = 'resonance'
                        elif line.startswith('LAST OBSERVED'):
                            last_observed = line.replace('LAST OBSERVED', '').strip().lstrip('-: ')
                            current_section = 'last'
                        elif line.startswith('ECHO'):
                            current_section = 'echo'
                        elif current_section == 'resonance' and line and not line.startswith('LAST'):
                            resonance += '\n' + line
                        elif current_section == 'echo' and line:
                            echo = line.strip('"').strip()

                    if name and resonance:
                        char_id = db.save_character(name, resonance, last_observed, echo, character_task or "Not specified")
                        st.success(f"✅ Saved to database - ID: {char_id}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")

        elif st.button("✨ Generate") and not character_name:
            st.warning("Please enter a character name")

    with tab2:
        st.header("📊 Character Database")

        if st.button("🔍 View All"):
            characters = db.get_all_characters()
            st.success(f"Found {len(characters)} characters")

            for char in characters:
                with st.expander(f"**{char['name']}** (ID: {char['id']})"):
                    st.markdown(f"**RESONANCE:**\n{char['resonance_types']}")
                    st.markdown(f"**LAST OBSERVED:** {char['last_observed']}")
                    st.markdown(f"**ECHO:** *{char['echo']}*")
                    st.markdown(f"**Task:** {char.get('character_task', 'N/A')}")
                    if st.button(f"🗑️ Delete", key=f"del_{char['id']}"):
                        db.delete_character(char['id'])
                        st.rerun()

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            query = st.text_input("Search by name or task")
            if st.button("🔍 Search") and query:
                results = db.search_characters(query)
                for c in results:
                    st.markdown(f"- **{c['name']}** - {c.get('character_task', 'N/A')}")

        with col2:
            char_id = st.number_input("Get by ID", min_value=1, step=1, value=1)
            if st.button("📋 Get"):
                char = db.get_character(int(char_id))
                if char:
                    st.json(char)
                else:
                    st.error("Not found")


if __name__ == "__main__":
    main()
