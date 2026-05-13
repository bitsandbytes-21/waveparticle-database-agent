#!/usr/bin/env python3
"""CLI tool for Character Profile Generator"""

import os
import sys
import argparse
from database import DatabaseAdapter
import google.generativeai as genai


def setup_gemini():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set")
        sys.exit(1)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')


def generate_character(character_name: str, context: str, model) -> dict:
    prompt = f"""Generate a character profile for: {character_name}
Context: {context}

Format:
NAME: 
[Full name]

RESONANCE TYPE: 
[5-7 resonance types: Existential, Reflective, Visionary, Melancholic, Defiant, Obsessive, Transcendent, Analytical, Creative, etc.]

LAST OBSERVED
[Location, Year]

ECHO(bio)
["Profound one-sentence quote they would say"]
"""
    response = model.generate_content(prompt)
    return parse_response(response.text)


def parse_response(text: str) -> dict:
    lines = text.strip().split('\n')
    result = {'name': '', 'resonance_types': '', 'last_observed': '', 'echo': ''}

    current = None
    buffer = []

    for line in lines:
        line = line.strip()
        if line.startswith('NAME:'):
            if current: result[current] = '\n'.join(buffer).strip()
            current = 'name'
            buffer = [line.replace('NAME:', '').strip()]
        elif line.startswith('TYPE:') or line.startswith('RESONANCE TYPE:') or line.startswith('RESONANCE:'):
            if current: result[current] = '\n'.join(buffer).strip()
            current = 'resonance_types'
            buffer = [line.split(':', 1)[1].strip()]
        elif line.startswith('LAST OBSERVED'):
            if current: result[current] = '\n'.join(buffer).strip()
            current = 'last_observed'
            buffer = [line.replace('LAST OBSERVED', '').strip().lstrip('- ')]
        elif line.startswith('ECHO'):
            if current: result[current] = '\n'.join(buffer).strip()
            current = 'echo'
            echo_text = line.split('ECHO', 1)[1].strip().lstrip('(bio):- ').strip('"').strip()
            buffer = [echo_text] if echo_text else []
        elif current == 'echo' and line.startswith('"'):
            buffer.append(line.strip('"'))
        elif current:
            buffer.append(line)

    if current: result[current] = '\n'.join(buffer).strip()
    return result


def main():
    parser = argparse.ArgumentParser(description="Character Profile Generator CLI")
    parser.add_argument('command', choices=['generate', 'list', 'get', 'delete'], help='Command to run')
    parser.add_argument('--name', help='Character name')
    parser.add_argument('--context', help='Character context')
    parser.add_argument('--id', type=int, help='Character ID')
    parser.add_argument('--db', default='characters.db', help='Database path')
    parser.add_argument('--save', action='store_true', help='Save to database')

    args = parser.parse_args()

    if args.command == 'generate':
        if not args.name:
            print("Error: --name required for generate command")
            sys.exit(1)

        model = setup_gemini()
        context = args.context or f"Create a profile for {args.name}"

        print(f"Generating profile for: {args.name}")
        profile = generate_character(args.name, context, model)

        print("\n" + "="*50)
        print("NAME:")
        print(profile['name'])
        print("\nRESONANCE TYPE:")
        print(profile['resonance_types'])
        print("\nLAST OBSERVED")
        print(profile['last_observed'])
        print("\nECHO(bio)")
        print(f'"{profile["echo"]}"')
        print("="*50)

        if args.save:
            db = DatabaseAdapter(args.db)
            db.init_db()
            char_id = db.save_character(
                profile['name'],
                profile['resonance_types'],
                profile['last_observed'],
                profile['echo']
            )
            print(f"\nSaved to database with ID: {char_id}")

    elif args.command == 'list':
        db = DatabaseAdapter(args.db)
        characters = db.get_all_characters()
        print(f"Total characters: {len(characters)}\n")
        for char in characters:
            print(f"[{char['id']}] {char['name']}")
            print(f"    Last observed: {char['last_observed']}")
            print()

    elif args.command == 'get':
        if not args.id:
            print("Error: --id required for get command")
            sys.exit(1)
        db = DatabaseAdapter(args.db)
        char = db.get_character(args.id)
        if char:
            print(f"NAME: {char['name']}")
            print(f"\nRESONANCE TYPE:\n{char['resonance_types']}")
            print(f"\nLAST OBSERVED: {char['last_observed']}")
            print(f"\nECHO: {char['echo']}")
            print(f"\nCreated: {char['created_at']}")
        else:
            print("Character not found")

    elif args.command == 'delete':
        if not args.id:
            print("Error: --id required for delete command")
            sys.exit(1)
        db = DatabaseAdapter(args.db)
        db.delete_character(args.id)
        print(f"Deleted character {args.id}")


if __name__ == "__main__":
    main()
