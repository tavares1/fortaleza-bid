import base64
import sys
import time
import io
from PIL import Image, ImageFilter
from google import genai
from google.genai import types
from app.config import Config

import json

class GeminiService:
    def __init__(self):
        self.api_key = Config.GOOGLE_API_KEY
        self.client = genai.Client(api_key=self.api_key)

    TEXT_MODELS = [
        'models/gemma-3-27b-it',
        'models/gemma-3-12b-it',
        'models/gemma-3-4b-it', 
        'models/gemma-3-1b-it',
        'models/gemini-2.5-flash',
    ]

    def _preprocess_image(self, image_bytes):
        """
        Converts image to grayscale and applies thresholding to remove noise.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("L")
            
            # Thresholding: pixels darker than 120 become 0 (black), others 255 (white)
            # This handles "dark, thick strokes" vs "light noise".
            # Adjust threshold as needed based on the sample image brightness.
            threshold = 120 
            img = img.point(lambda p: 0 if p < threshold else 255)
            
            # Save preprocessed debug image
            img.save("last_captcha_processed.png")
            
            # Convert back to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
        except Exception as e:
            print(f"Error processing image: {e}")
            return image_bytes

    def _generate_with_retry(self, contents, temperature=0.0, is_vision=False):
        """
        Robust generation with model rotation and waiting strategy.
        """
        models = self.TEXT_MODELS
        
        max_cycles = 2 # How many times to cycle through the entire list
        cycle_count = 0
        
        while cycle_count < max_cycles:
            for model in models:
                try:
                    # Clean model name if needed (sometimes 'models/' prefix is optional but genai usually handles it)
                    print(f"Attempting to generate content using model: {model}")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=types.GenerateContentConfig(temperature=temperature)
                    )
                    return response.text.strip()
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "resource_exhausted" in error_str or "exhausted" in error_str:
                        print(f"Model {model} exhausted (429). Trying next model...")
                        time.sleep(0.5) 
                        continue
                    elif "404" in error_str or "not_found" in error_str:
                        print(f"Model {model} not found (404). Removing from list and trying next...")
                        # Optional: Remove from list to avoid hitting it again in next cycle
                        # models.remove(model) # Dangerous to modify list while iterating
                        continue
                    else:
                        print(f"Error calling Gemini with model {model}: {e}")
                        continue
            
            # If we exit the for loop, it means ALL models failed in this cycle
            cycle_count += 1
            if cycle_count < max_cycles:
                print("All models exhausted. Waiting 60 seconds before next cycle...")
                time.sleep(60)
            else:
                print("Max retry cycles reached. All models failed.")
        
        raise Exception("All models failed after retries.")

    def solve_captcha(self, base64_image_str):
        clean_base64 = base64_image_str.strip('"').strip()
        
        try:
            image_bytes = base64.b64decode(clean_base64)
            
            # Preprocess image (remove noise)
            processed_bytes = self._preprocess_image(image_bytes)
            
            # Save for debugging
            with open("last_captcha.png", "wb") as f:
                f.write(image_bytes)
            print("Saved captcha image to last_captcha.png")
            
        except Exception as e:
            print(f"Error decoding base64: {e}")
            sys.exit(1)
        
        prompt = """
        Act as a robust OCR system designed to solve noisy CAPTCHAs. Analyze the provided image focusing on the BLACK characters against the WHITE background.

Instructions:
1. Identifying exactly 4 uppercase letters (A-Z).
2. Do not include numbers; strictly output letters.
3. The characters are thick and dark.

Output: Return ONLY the 4 letters found, with no additional text or whitespace.
        """

        text = self._generate_with_retry(
            contents=[
                types.Part.from_text(text=prompt),
                types.Part.from_bytes(data=processed_bytes, mime_type="image/png")
            ],
            temperature=0.0,
            is_vision=True
        )
        # Clean result (keep only alphanumeric, max 4 chars)
        import re
        clean_text = re.sub(r'[^a-zA-Z0-9]', '', text)
        return clean_text[:4].upper()

    def generate_tweet_text(self, contract_data):
        """
        Generates a creative tweet about the contract.
        """
    
        # Prepare data for JSON serialization (remove ObjectId)
        data_for_prompt = contract_data.copy()
        if '_id' in data_for_prompt:
            del data_for_prompt['_id']
        
        json_input = json.dumps(data_for_prompt, indent=2, ensure_ascii=False, default=str)

        prompt_text = f"""
        # ROLE
Você é o "Leão do BID", o setorista digital do Fortaleza Esporte Clube. Sua função é anunciar novas contratações e movimentações no BID da CBF para o Twitter (X), agindo não apenas como um notificador, mas como um analista que explica ao torcedor quem é o jogador que está chegando.

# TASK
Analise o JSON do BID. Se for "Contrato Definitivo", trate como uma **NOVA CONTRATAÇÃO (COMPRA/AQUISIÇÃO)**. Analise o histórico de partidas fornecido para traçar um perfil rápido do atleta (se é titular, se faz gols, se é indisciplinado) e gerar valor na notícia.

# STEP-BY-STEP PROCESS (Chain of Thought)

1.  **CLASSIFICAÇÃO DO NEGÓCIO (Regra de Ouro)**:
    * **Contrato Definitivo**: O atleta foi **ADQUIRIDO/COMPRADO**. É um **REFORÇO** chegando ao Pici. Nunca trate como renovação. Use termos como "É DO LEÃO", "REFORÇO", "NOVO CONTRATADO".
    * **Empréstimo**: Reforço chegando por tempo determinado.
    * **Rescisão**: Saída de jogador.

2.  **ANÁLISE DE SCOUT (Mineração do `historico`)**:
    * Olhe para os jogos mais recentes no array `historico`. O objetivo é responder: "Como esse cara vem jogando?".
    * **Ritmo de Jogo**:
        * Se tem muitos jogos recentes: "Chega com ritmo de jogo".
        * Se tem poucos jogos: "Busca recuperar espaço".
    * **Perfil Tático (Titular vs Reserva)**:
        * Verifique o array `alteracoes` dentro dos jogos.
        * Se o atleta aparece muito como "ENTROU": Ele costuma ser **opção de segundo tempo**.
        * Se ele joga e não aparece em "ENTROU" (ou aparece como "SAIU" no fim): Ele costuma ser **titular**.
    * **Disciplina e Gols**:
        * Verifique `penalidades` (Cartões). Média alta = "Jogador de pegada forte/intenso".
        * Verifique `gols`. Se tiver, destaque o "faro de gol".

3.  **FORMATAÇÃO VISUAL (Padrão Twitter)**:
    * Converta a **Manchete** e o **Nome do Jogador** para Unicode Matemático Sans-Serif Negrito (ex: 𝐑𝐄𝐅𝐎𝐑𝐂̧𝐎).
    * Substitua "Fortaleza" por **@fortalezaec**.

4.  **MONTAGEM DO TWEET**:
    * **Linha 1:** Emoji (🦁, ✍️, 🆕, 📝, 📊, 🔴🔵⚪ ) + [MANCHETE EM UNICODE NEGRITO].
    * **Linha 3:** Anuncie a compra/chegada do atleta [Nome em Unicode] ao @fortalezaec.
    * **Linha 5 (O Pulo do Gato):** A análise feita no passo 2. Ex: "O reforço chega com status de titular..." ou "Vinha sendo utilizado como opção para o 2º tempo em sua última temporada..."
    * **Linha 7:** #FortalezaEC #BID #LeãoDoPici

# JSON INPUT
"""+json_input+"""
# OUTPUT FORMAT
Apenas o texto final do tweet.
        """

        try:
            return self._generate_with_retry(contents=[types.Part.from_text(text=prompt_text)], is_vision=False)
        except Exception as e:
            print(f"Error generating tweet with Gemini: {e}")
            # Fallback text if AI fails
            nome = contract_data.get('nome', 'Jogador')
            apelido = contract_data.get('apelido', 'Desconhecido')
            tipo_contrato = contract_data.get('tipo_contrato', '')
            return f"BID Publicado: {nome} ({apelido}) - {tipo_contrato}. #FortalezaEC"
