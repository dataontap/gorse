
import os
import requests
import json
from datetime import datetime

class ElevenLabsService:
    def __init__(self):
        # Try the correct environment variable name first, with fallback for backward compatibility
        self.api_key = os.environ.get('ELEVENLABS_API_KEY') or os.environ.get('ElevenLabs_Key')
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Log if API key is missing for easier debugging
        if not self.api_key:
            print("WARNING: ElevenLabs API key not found in environment variables (ELEVENLABS_API_KEY or ElevenLabs_Key)")
        else:
            print("ElevenLabs API key configured successfully")
        
    def get_voices(self):
        """Get available voices from ElevenLabs"""
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            response = requests.get(f"{self.base_url}/voices", headers=headers)
            response.raise_for_status()
            
            return response.json().get('voices', [])
        except Exception as e:
            print(f"Error getting voices: {str(e)}")
            return []
    
    def generate_welcome_message(self, user_name=None, language="en", voice_id=None):
        """Generate personalized welcome message text"""
        now = datetime.now()
        day_name = now.strftime("%A")
        date_str = now.strftime("%B %d, %Y")
        
        # Default voice if none specified
        if not voice_id:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        
        # Generate message based on language
        messages = {
            "en": self._generate_english_message(user_name, day_name, date_str),
            "es": self._generate_spanish_message(user_name, day_name, date_str),
            "fr": self._generate_french_message(user_name, day_name, date_str)
        }
        
        message_text = messages.get(language, messages["en"])
        
        return self.text_to_speech(message_text, voice_id, language)
    
    def _generate_english_message(self, user_name, day_name, date_str):
        name_part = ""
        if user_name:
            name_part = f"Hello {user_name}! Am I pronouncing your name correctly? "
        
        return f"""
        {name_part}Welcome to DOT Mobile! Today is {day_name}, {date_str}, and we're thrilled to have you join our global connectivity network.
        
        You've just become part of something revolutionary - a wireless service that works everywhere on Earth and even up to 15 kilometers above it. Whether you're traveling across continents or exploring new heights, we've got you covered.
        
        Your account is now active with premium global data connectivity. You can purchase data packages, manage your eSIM profiles, and access our network features right from your dashboard. 
        
        We've awarded you some DOTM tokens as a welcome bonus - these are your gateway to exclusive features and rewards within our ecosystem. Think of them as your digital passport to better connectivity.
        
        Our Canadian full MVNO service means you're not just getting coverage - you're getting carrier-grade reliability with the flexibility of a modern digital platform. From the bustling streets of Toronto to remote locations worldwide, your connection stays strong.
        
        Take a moment to explore your dashboard. You'll find your data balance, network settings, and marketplace where you can discover new connectivity options. Don't forget to check out our notifications section for updates and exclusive offers.
        
        If you have any questions, our AI assistant is always ready to help, or you can request a callback from our human support team. We're here to make sure your global connectivity experience is seamless.
        
        Welcome aboard, and enjoy exploring the world while staying perfectly connected!
        """
    
    def _generate_spanish_message(self, user_name, day_name, date_str):
        name_part = ""
        if user_name:
            name_part = f"¡Hola {user_name}! ¿Estoy pronunciando tu nombre correctamente? "
        
        return f"""
        {name_part}¡Bienvenido a DOT Mobile! Hoy es {day_name}, {date_str}, y estamos emocionados de tenerte en nuestra red de conectividad global.
        
        Acabas de formar parte de algo revolucionario: un servicio inalámbrico que funciona en toda la Tierra e incluso hasta 15 kilómetros de altura. Ya sea que viajes entre continentes o explores nuevas alturas, te tenemos cubierto.
        
        Tu cuenta está activa con conectividad premium de datos globales. Puedes comprar paquetes de datos, gestionar tus perfiles eSIM y acceder a las funciones de nuestra red desde tu panel de control.
        
        Te hemos otorgado algunos tokens DOTM como bono de bienvenida: estos son tu puerta de entrada a funciones exclusivas y recompensas dentro de nuestro ecosistema.
        
        Nuestro servicio MVNO canadiense completo significa que no solo obtienes cobertura, sino confiabilidad de nivel carrier con la flexibilidad de una plataforma digital moderna.
        
        ¡Bienvenido a bordo y disfruta explorando el mundo mientras te mantienes perfectamente conectado!
        """
    
    def _generate_french_message(self, user_name, day_name, date_str):
        name_part = ""
        if user_name:
            name_part = f"Bonjour {user_name}! Est-ce que je prononce votre nom correctement? "
        
        return f"""
        {name_part}Bienvenue chez DOT Mobile! Nous sommes aujourd'hui {day_name}, {date_str}, et nous sommes ravis de vous accueillir dans notre réseau de connectivité mondiale.
        
        Vous venez de faire partie de quelque chose de révolutionnaire - un service sans fil qui fonctionne partout sur Terre et même jusqu'à 15 kilomètres d'altitude. Que vous voyagiez entre continents ou exploriez de nouveaux horizons, nous vous couvrons.
        
        Votre compte est maintenant actif avec une connectivité de données mondiale premium. Vous pouvez acheter des forfaits de données, gérer vos profils eSIM et accéder aux fonctionnalités de notre réseau depuis votre tableau de bord.
        
        Nous vous avons attribué quelques tokens DOTM comme bonus de bienvenue - ils sont votre passerelle vers des fonctionnalités exclusives et des récompenses dans notre écosystème.
        
        Notre service MVNO canadien complet signifie que vous n'obtenez pas seulement une couverture - vous obtenez une fiabilité de niveau opérateur avec la flexibilité d'une plateforme numérique moderne.
        
        Bienvenue à bord et amusez-vous à explorer le monde tout en restant parfaitement connecté!
        """
    
    def text_to_speech(self, text, voice_id, language="en"):
        """Convert text to speech using ElevenLabs API"""
        try:
            # First verify the API key is available
            if not self.api_key:
                print("ERROR: No ElevenLabs API key available for text-to-speech")
                return {"success": False, "error": "No API key configured"}
            
            # Verify the voice ID exists in available voices
            available_voices = self.get_voices()
            voice_ids = [voice.get('voice_id') for voice in available_voices]
            print(f"DEBUG: Available voice IDs: {voice_ids}")
            print(f"DEBUG: Requested voice ID: {voice_id}")
            
            if voice_id not in voice_ids and available_voices:
                print(f"WARNING: Voice ID {voice_id} not found in available voices, using default")
                voice_id = voice_ids[0] if voice_ids else "21m00Tcm4TlvDq8ikWAM"
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            print(f"DEBUG: Making TTS request to: {url}")
            
            # Voice settings for different tones
            voice_settings = {
                "stability": 0.75,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": voice_settings
            }
            
            print(f"DEBUG: Request headers (API key masked): {dict(headers, **{'xi-api-key': '***MASKED***'})}")
            print(f"DEBUG: Request data: {dict(data, text='[TEXT TRUNCATED]')}")
            
            response = requests.post(url, json=data, headers=headers)
            print(f"DEBUG: Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"DEBUG: Response headers: {dict(response.headers)}")
                print(f"DEBUG: Response body: {response.text}")
            
            response.raise_for_status()
            
            return {
                "success": True,
                "audio_data": response.content,
                "content_type": "audio/mpeg"
            }
            
        except Exception as e:
            print(f"Error generating speech: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_voice_settings(self, voice_id):
        """Get voice settings for a specific voice"""
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            response = requests.get(f"{self.base_url}/voices/{voice_id}/settings", headers=headers)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"Error getting voice settings: {str(e)}")
            return None

# Initialize service
elevenlabs_service = ElevenLabsService()
