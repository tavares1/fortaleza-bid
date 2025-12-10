import base64
import sys
import time
import io
from PIL import Image, ImageFilter
from google import genai
from google.genai import types
from app.config import Config

class GeminiService:
    def __init__(self):
        self.api_key = Config.GOOGLE_API_KEY
        self.client = genai.Client(api_key=self.api_key)

    MODELS = [
        'gemma-3-27b-it',
        'gemma-3-12b-it',
        'gemma-3-4b-it',
        'gemma-3-1b-it'
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

    def _generate_with_retry(self, contents, temperature=0.0):
        for model in self.MODELS:
            try:
                print(f"Attempting to generate content using model: {model}")
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(temperature=temperature)
                )
                return response.text.strip()
            except Exception as e:
                # ... existing error handling ...
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"Model {model} exhausted (429). Trying next model...")
                    time.sleep(1) # Small delay to be safe
                    continue
                else:
                    # If it's another error, we might want to fail or retry? 
                    # User only specified 429 behavior. 
                    # Let's assume other errors are blocking for that model but we could try others?
                    # Usually 429 is the only one suggesting "try another resource".
                    # Let's re-raise if it's not 429 to avoid masking real bugs, 
                    # OR we can treat it as a model failure and try next.
                    # Given the instruction "when generation returns 429... try next", strict interpretation
                    # implies only 429 triggers fallback. But robust code often falls back on 5xx too.
                    # I will stick to 429 as requested.
                    print(f"Error calling Gemini with model {model}: {e}")
                    raise e
        
        raise Exception("All models failed with 429/Resource Exhausted.")

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
            temperature=0.0
        )
        # Clean result (keep only alphanumeric, max 4 chars)
        import re
        clean_text = re.sub(r'[^a-zA-Z0-9]', '', text)
        return clean_text[:4].upper()

    def generate_tweet_text(self, contract_data):
        """
        Generates a creative tweet about the contract.
        """
        from datetime import datetime
        
        # Extract relevant info
        nome = contract_data.get('nome', 'N/A')
        apelido = contract_data.get('apelido', '')
        clube = contract_data.get('clube', 'Fortaleza')
        tipo_contrato = contract_data.get('tipocontrato', 'Contrato') # Corrected key likely 'tipocontrato' based on prev logs
        data_nasc = contract_data.get('data_nascimento', '')
        uf = contract_data.get('uf', '')
        
        # Calculate Age
        idade = "N/A"
        if data_nasc:
            try:
                birth_date = datetime.strptime(data_nasc, "%Y-%m-%d")
                today = datetime.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                idade = f"{age} anos"
            except:
                pass

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
    * **Linha 1:** Emoji (🦁, ✍️, 🆕) + [MANCHETE EM UNICODE NEGRITO].
    * **Linha 3:** Anuncie a compra/chegada do atleta [Nome em Unicode] ao @fortalezaec.
    * **Linha 5 (O Pulo do Gato):** A análise feita no passo 2. Ex: "O reforço chega com status de titular..." ou "Vinha sendo utilizado como opção para o 2º tempo em sua última temporada..."
    * **Linha 7:** #FortalezaEC #BID #LeãoDoPici

# JSON INPUT
{{JSON_DO_USUARIO}}

# OUTPUT FORMAT
Apenas o texto final do tweet.
        """

        try:
            return self._generate_with_retry(contents=[types.Part.from_text(text=prompt_text)])
        except Exception as e:
            print(f"Error generating tweet with Gemini: {e}")
            # Fallback text if AI fails
            return f"BID Publicado: {nome} ({apelido}) - {tipo_contrato}. #FortalezaEC"
