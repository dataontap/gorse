
import os
import requests
import json
from datetime import datetime

class ElevenLabsService:
    def __init__(self):
        # Try the correct environment variable name first, with fallback for backward compatibility
        self.api_key = os.environ.get('ELEVENLABS_API_KEY') or os.environ.get('ElevenLabs_Key')
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Define custom voice profiles
        self.voice_profiles = {
            "CanadianRockstar": {
                "name": "CanadianRockstar",
                "description": "Deep, raspy male voice with character",
                "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam - deep, engaging
                "settings": {
                    "stability": 0.65,
                    "similarity_boost": 0.80,
                    "style": 0.60,
                    "use_speaker_boost": True
                }
            },
            "ScienceTeacher": {
                "name": "ScienceTeacher",
                "description": "Clear, professional female educational voice",
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella - clear, articulate
                "settings": {
                    "stability": 0.80,
                    "similarity_boost": 0.75,
                    "style": 0.40,
                    "use_speaker_boost": True
                }
            },
            "BuddyFriend": {
                "name": "BuddyFriend",
                "description": "Friendly, energetic casual voice",
                "voice_id": "nPczCjzI2devNBz1zQrb",  # Brian - young, friendly
                "settings": {
                    "stability": 0.70,
                    "similarity_boost": 0.70,
                    "style": 0.55,
                    "use_speaker_boost": True
                }
            }
        }
        
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
    
    def get_voice_profiles(self):
        """Return available voice profiles"""
        return self.voice_profiles
    
    def get_voice_for_profile(self, profile_name):
        """Get voice ID and settings for a specific profile"""
        profile = self.voice_profiles.get(profile_name)
        if profile:
            return profile["voice_id"], profile["settings"]
        return None, None
    
    def generate_welcome_message(self, user_name=None, language="en", voice_profile="ScienceTeacher", message_type="welcome", location_data=None, events_data=None, time_data=None, context_data=None):
        """Generate personalized message text based on message type"""
        now = datetime.now()
        day_name = now.strftime("%A")
        date_str = now.strftime("%B %d, %Y")
        
        # Get voice settings from profile
        voice_id, voice_settings = self.get_voice_for_profile(voice_profile)
        if not voice_id:
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default Rachel voice
            voice_settings = None
        
        # Language message generators by type
        if message_type == "welcome":
            language_generators = {
                "en": self._generate_english_message,
                "es": self._generate_spanish_message,
                "fr": self._generate_french_message,
                "de": self._generate_german_message,
                "it": self._generate_italian_message,
                "pt": self._generate_portuguese_message,
                "nl": self._generate_dutch_message,
                "pl": self._generate_polish_message,
                "ar": self._generate_arabic_message,
                "hi": self._generate_hindi_message,
                "ja": self._generate_japanese_message,
                "ko": self._generate_korean_message,
                "zh": self._generate_chinese_message,
                "ru": self._generate_russian_message,
                "tr": self._generate_turkish_message,
                "sv": self._generate_swedish_message,
                "no": self._generate_norwegian_message,
                "da": self._generate_danish_message,
                "fi": self._generate_finnish_message,
                "cs": self._generate_czech_message,
                "ro": self._generate_romanian_message,
                "el": self._generate_greek_message,
                "he": self._generate_hebrew_message,
                "th": self._generate_thai_message,
                "vi": self._generate_vietnamese_message,
                "id": self._generate_indonesian_message,
                "ms": self._generate_malay_message,
                "fil": self._generate_filipino_message,
                "uk": self._generate_ukrainian_message,
                "bg": self._generate_bulgarian_message
            }
        elif message_type == "tip":
            language_generators = {
                "en": self._generate_english_tip,
                "es": self._generate_spanish_tip,
                "fr": self._generate_french_tip,
            }
        elif message_type == "update":
            language_generators = {
                "en": self._generate_english_update,
                "es": self._generate_spanish_update,
                "fr": self._generate_french_update,
            }
        else:
            # Default to welcome
            language_generators = {
                "en": self._generate_english_message,
            }
        
        # Get message generator or fallback to English
        generator = language_generators.get(language, language_generators.get("en", self._generate_english_message))
        message_text = generator(user_name, day_name, date_str, location_data, events_data, time_data, context_data)
        
        return self.text_to_speech(message_text, voice_id, language, voice_settings)
    
    def _generate_english_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        # Build location and time specific greeting
        location_time_part = ""
        if location_data and location_data.get('success'):
            city = location_data.get('city', '')
            region = location_data.get('region', '')
            country = location_data.get('country', '')
            
            if city:
                location_time_part = f" I can see you're joining us from {city}"
                if region and region != city:
                    location_time_part += f", {region}"
                if country:
                    location_time_part += f", {country}"
                
                # Add local time if available
                if time_data and time_data.get('success'):
                    time_of_day = time_data.get('time_of_day', '')
                    time_12h = time_data.get('time_12h', '')
                    if time_of_day and time_12h:
                        location_time_part += f" at {time_12h} on this {time_of_day}"
                
                location_time_part += "."
        
        # Build context part (weather, traffic, events from Gemini)
        context_part = ""
        if context_data and context_data.get('success'):
            summary = context_data.get('summary', '')
            if summary:
                context_part = f"\n\n{summary}"
        
        # Build ISP part
        isp_part = ""
        if location_data and location_data.get('success'):
            isp = location_data.get('isp', '')
            if isp:
                isp_part = f"\n\nI notice you're connecting through {isp}. Even before becoming a full member with an annual membership, you're already gaining insights about your network connectivity just by joining our community."
        
        # Build name acknowledgment (after brand message)
        name_acknowledgment = ""
        if user_name:
            name_acknowledgment = f"\n\nHello {user_name}! I hope I'm pronouncing your name correctly."
        
        return f"""
        Welcome to our community. We are building the connectivity network of the future for Canadians anywhere.{location_time_part}
        {context_part}
        {isp_part}
        {name_acknowledgment}
        
        You've just become part of something revolutionary - a wireless service that works everywhere on Earth and even up to 15 kilometers above it. Whether you're traveling across continents or exploring new heights, we've got you covered.
        
        Your account is now active with premium global data connectivity. You can purchase data packages, manage your eSIM profiles, and access our network features right from your dashboard. 
        
        We've awarded you some DOTM tokens as a welcome bonus - these are your gateway to exclusive features and rewards within our ecosystem. Think of them as your digital passport to better connectivity.
        
        Our Canadian full MVNO service means you're not just getting coverage - you're getting carrier-grade reliability with the flexibility of a modern digital platform. From the bustling streets of Toronto to remote locations worldwide, your connection stays strong.
        
        Take a moment to explore your dashboard. You'll find your data balance, network settings, and marketplace where you can discover new connectivity options. Don't forget to check out our notifications section for updates and exclusive offers.
        
        If you have any questions, our AI assistant is always ready to help, or you can request a callback from our human support team. We're here to make sure your global connectivity experience is seamless.
        
        Welcome aboard, and enjoy exploring the world while staying perfectly connected!
        """
    
    def _generate_spanish_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
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
    
    def _generate_french_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
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
    
    def _generate_german_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Hallo {user_name}! Spreche ich Ihren Namen richtig aus? " if user_name else ""
        return f"{name_part}Willkommen bei DOT Mobile! Heute ist {day_name}, {date_str}, und wir freuen uns sehr, Sie in unserem globalen Konnektivitätsnetzwerk begrüßen zu dürfen. Sie sind jetzt Teil von etwas Revolutionärem - einem drahtlosen Dienst, der überall auf der Erde funktioniert. Viel Spaß beim Erkunden der Welt, während Sie perfekt verbunden bleiben!"
    
    def _generate_italian_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Ciao {user_name}! Sto pronunciando correttamente il tuo nome? " if user_name else ""
        return f"{name_part}Benvenuto su DOT Mobile! Oggi è {day_name}, {date_str}, e siamo entusiasti di averti nella nostra rete di connettività globale. Sei appena diventato parte di qualcosa di rivoluzionario. Benvenuto a bordo e goditi l'esplorazione del mondo rimanendo perfettamente connesso!"
    
    def _generate_portuguese_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Olá {user_name}! Estou pronunciando seu nome corretamente? " if user_name else ""
        return f"{name_part}Bem-vindo ao DOT Mobile! Hoje é {day_name}, {date_str}, e estamos emocionados por você se juntar à nossa rede de conectividade global. Você acabou de fazer parte de algo revolucionário. Bem-vindo a bordo e aproveite explorando o mundo enquanto permanece perfeitamente conectado!"
    
    def _generate_dutch_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Hallo {user_name}! Spreek ik uw naam correct uit? " if user_name else ""
        return f"{name_part}Welkom bij DOT Mobile! Vandaag is het {day_name}, {date_str}, en we zijn verheugd om u te verwelkomen in ons wereldwijde connectiviteitsnetwerk. U bent nu deel van iets revolutionairs. Welkom aan boord en geniet van het verkennen van de wereld terwijl u perfect verbonden blijft!"
    
    def _generate_polish_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Cześć {user_name}! Czy poprawnie wymawiam twoje imię? " if user_name else ""
        return f"{name_part}Witamy w DOT Mobile! Dzisiaj jest {day_name}, {date_str}, i jesteśmy podekscytowani, że dołączasz do naszej globalnej sieci łączności. Właśnie stałeś się częścią czegoś rewolucyjnego. Witamy na pokładzie i ciesz się odkrywaniem świata, pozostając doskonale połączonym!"
    
    def _generate_arabic_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"مرحباً {user_name}! هل أنطق اسمك بشكل صحيح؟ " if user_name else ""
        return f"{name_part}مرحباً بك في DOT Mobile! اليوم هو {day_name}، {date_str}، ونحن متحمسون لانضمامك إلى شبكة الاتصال العالمية لدينا. لقد أصبحت جزءاً من شيء ثوري. مرحباً بك على متن الطائرة واستمتع باستكشاف العالم أثناء البقاء متصلاً بشكل مثالي!"
    
    def _generate_hindi_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"नमस्ते {user_name}! क्या मैं आपका नाम सही से बोल रहा हूं? " if user_name else ""
        return f"{name_part}DOT Mobile में आपका स्वागत है! आज {day_name}, {date_str} है, और हम आपको हमारे वैश्विक कनेक्टिविटी नेटवर्क में शामिल होने के लिए रोमांचित हैं। आप कुछ क्रांतिकारी का हिस्सा बन गए हैं। स्वागत है और पूरी तरह से जुड़े रहते हुए दुनिया की खोज का आनंद लें!"
    
    def _generate_japanese_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"こんにちは{user_name}さん！お名前の発音は正しいですか？ " if user_name else ""
        return f"{name_part}DOT Mobileへようこそ！今日は{day_name}、{date_str}です。グローバル接続ネットワークへの参加を歓迎します。あなたは革命的な何かの一部になりました。ようこそ、完璧に接続されたまま世界を探索することをお楽しみください！"
    
    def _generate_korean_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"안녕하세요 {user_name}님! 제가 이름을 올바르게 발음하고 있나요? " if user_name else ""
        return f"{name_part}DOT Mobile에 오신 것을 환영합니다! 오늘은 {day_name}, {date_str}입니다. 글로벌 연결 네트워크에 참여하게 되어 기쁩니다. 당신은 혁명적인 무언가의 일부가 되었습니다. 환영합니다. 완벽하게 연결된 상태에서 세계를 탐험하는 것을 즐기십시오!"
    
    def _generate_chinese_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"你好{user_name}！我的发音正确吗？ " if user_name else ""
        return f"{name_part}欢迎来到DOT Mobile！今天是{day_name}，{date_str}，我们很高兴您加入我们的全球连接网络。您刚刚成为革命性事物的一部分。欢迎加入，享受在保持完美连接的同时探索世界！"
    
    def _generate_russian_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Здравствуйте {user_name}! Я правильно произношу ваше имя? " if user_name else ""
        return f"{name_part}Добро пожаловать в DOT Mobile! Сегодня {day_name}, {date_str}, и мы рады приветствовать вас в нашей глобальной сети подключения. Вы только что стали частью чего-то революционного. Добро пожаловать на борт и наслаждайтесь исследованием мира, оставаясь идеально подключенными!"
    
    def _generate_turkish_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Merhaba {user_name}! Adınızı doğru telaffuz ediyor muyum? " if user_name else ""
        return f"{name_part}DOT Mobile'a hoş geldiniz! Bugün {day_name}, {date_str} ve küresel bağlantı ağımıza katılmanızdan heyecan duyuyoruz. Devrimci bir şeyin parçası oldunuz. Hoş geldiniz ve mükemmel şekilde bağlı kalırken dünyayı keşfetmenin tadını çıkarın!"
    
    def _generate_swedish_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Hej {user_name}! Uttalar jag ditt namn korrekt? " if user_name else ""
        return f"{name_part}Välkommen till DOT Mobile! Idag är det {day_name}, {date_str}, och vi är glada att välkomna dig till vårt globala anslutningsnätverk. Du har precis blivit en del av något revolutionerande. Välkommen ombord och njut av att utforska världen samtidigt som du förblir perfekt ansluten!"
    
    def _generate_norwegian_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Hei {user_name}! Uttaler jeg navnet ditt riktig? " if user_name else ""
        return f"{name_part}Velkommen til DOT Mobile! I dag er det {day_name}, {date_str}, og vi er glade for å ønske deg velkommen til vårt globale tilkoblingsnettverk. Du har nettopp blitt en del av noe revolusjonerende. Velkommen om bord og nyt å utforske verden mens du forblir perfekt tilkoblet!"
    
    def _generate_danish_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Hej {user_name}! Udtaler jeg dit navn korrekt? " if user_name else ""
        return f"{name_part}Velkommen til DOT Mobile! I dag er det {day_name}, {date_str}, og vi er glade for at byde dig velkommen til vores globale forbindelsesnetværk. Du er lige blevet en del af noget revolutionerende. Velkommen ombord og nyd at udforske verden, mens du forbliver perfekt forbundet!"
    
    def _generate_finnish_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Hei {user_name}! Äänänkö nimesi oikein? " if user_name else ""
        return f"{name_part}Tervetuloa DOT Mobileen! Tänään on {day_name}, {date_str}, ja olemme innoissamme toivottaessamme sinut tervetulleeksi maailmanlaajuiseen yhteysverkostoomme. Olet juuri tullut osaksi jotain vallankumouksellista. Tervetuloa kyytiin ja nauti maailman tutkimisesta pysyen täydellisesti yhteydessä!"
    
    def _generate_czech_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Ahoj {user_name}! Vyslovuji tvoje jméno správně? " if user_name else ""
        return f"{name_part}Vítejte v DOT Mobile! Dnes je {day_name}, {date_str}, a jsme rádi, že vás můžeme přivítat v naší globální síti připojení. Právě jste se stali součástí něčeho revolučního. Vítejte na palubě a užijte si zkoumání světa, zatímco zůstanete dokonale připojeni!"
    
    def _generate_romanian_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Bună {user_name}! Pronunț corect numele tău? " if user_name else ""
        return f"{name_part}Bun venit la DOT Mobile! Astăzi este {day_name}, {date_str}, și suntem încântați să vă primim în rețeaua noastră globală de conectivitate. Tocmai ați devenit parte dintr-un lucru revoluționar. Bun venit la bord și bucurați-vă de explorarea lumii rămânând perfect conectat!"
    
    def _generate_greek_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Γεια σου {user_name}! Προφέρω σωστά το όνομά σου; " if user_name else ""
        return f"{name_part}Καλώς ήρθατε στο DOT Mobile! Σήμερα είναι {day_name}, {date_str}, και είμαστε ενθουσιασμένοι που σας καλωσορίζουμε στο παγκόσμιο δίκτυο συνδεσιμότητάς μας. Μόλις γίνατε μέρος κάτι επαναστατικού. Καλώς ήρθατε και απολαύστε την εξερεύνηση του κόσμου ενώ παραμένετε τέλεια συνδεδεμένοι!"
    
    def _generate_hebrew_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"שלום {user_name}! האם אני מבטא את שמך נכון? " if user_name else ""
        return f"{name_part}ברוכים הבאים ל-DOT Mobile! היום הוא {day_name}, {date_str}, ואנחנו נרגשים לקבל אתכם לרשת הקישוריות הגלובלית שלנו. הרגע הפכתם לחלק ממשהו מהפכני. ברוכים הבאים ותהנו לחקור את העולם תוך שמירה על חיבור מושלם!"
    
    def _generate_thai_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"สวัสดี {user_name}! ฉันออกเสียงชื่อคุณถูกต้องไหม? " if user_name else ""
        return f"{name_part}ยินดีต้อนรับสู่ DOT Mobile! วันนี้คือ {day_name}, {date_str} และเรายินดีที่จะต้อนรับคุณเข้าสู่เครือข่ายการเชื่อมต่อทั่วโลกของเรา คุณเพิ่งกลายเป็นส่วนหนึ่งของบางสิ่งที่ปฏิวัติ ยินดีต้อนรับและสนุกกับการสำรวจโลกในขณะที่เชื่อมต่ออย่างสมบูรณ์แบบ!"
    
    def _generate_vietnamese_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Xin chào {user_name}! Tôi có phát âm tên của bạn đúng không? " if user_name else ""
        return f"{name_part}Chào mừng đến với DOT Mobile! Hôm nay là {day_name}, {date_str}, và chúng tôi rất vui mừng chào đón bạn vào mạng kết nối toàn cầu của chúng tôi. Bạn vừa trở thành một phần của điều gì đó mang tính cách mạng. Chào mừng và tận hưởng việc khám phá thế giới trong khi vẫn kết nối hoàn hảo!"
    
    def _generate_indonesian_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Halo {user_name}! Apakah saya mengucapkan nama Anda dengan benar? " if user_name else ""
        return f"{name_part}Selamat datang di DOT Mobile! Hari ini adalah {day_name}, {date_str}, dan kami senang menyambut Anda ke jaringan konektivitas global kami. Anda baru saja menjadi bagian dari sesuatu yang revolusioner. Selamat datang dan nikmati menjelajahi dunia sambil tetap terhubung dengan sempurna!"
    
    def _generate_malay_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Halo {user_name}! Adakah saya menyebut nama anda dengan betul? " if user_name else ""
        return f"{name_part}Selamat datang ke DOT Mobile! Hari ini ialah {day_name}, {date_str}, dan kami teruja untuk mengalu-alukan anda ke rangkaian sambungan global kami. Anda baru sahaja menjadi sebahagian daripada sesuatu yang revolusioner. Selamat datang dan nikmatilah meneroka dunia sambil kekal bersambung dengan sempurna!"
    
    def _generate_filipino_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Kamusta {user_name}! Tama ba ang pagbigkas ko sa iyong pangalan? " if user_name else ""
        return f"{name_part}Maligayang pagdating sa DOT Mobile! Ngayong araw ay {day_name}, {date_str}, at nasasabik kaming tanggapin ka sa aming pandaigdigang network ng koneksyon. Ikaw ay naging bahagi ng isang rebolusyonaryong bagay. Maligayang pagdating at tamasahin ang paggalugad sa mundo habang nananatiling perpektong konektado!"
    
    def _generate_ukrainian_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Привіт {user_name}! Чи правильно я вимовляю ваше ім'я? " if user_name else ""
        return f"{name_part}Ласкаво просимо до DOT Mobile! Сьогодні {day_name}, {date_str}, і ми раді вітати вас у нашій глобальній мережі зв'язку. Ви щойно стали частиною чогось революційного. Ласкаво просимо і насолоджуйтесь дослідженням світу, залишаючись ідеально підключеними!"
    
    def _generate_bulgarian_message(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        name_part = f"Здравей {user_name}! Произнасям ли правилно името ти? " if user_name else ""
        return f"{name_part}Добре дошли в DOT Mobile! Днес е {day_name}, {date_str}, и сме развълнувани да ви приветстваме в нашата глобална мрежа за свързаност. Току-що станахте част от нещо революционно. Добре дошли и се насладете на изследването на света, докато оставате перфектно свързани!"
    
    # TIP MESSAGE GENERATORS
    def _generate_english_tip(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        return f"""
        Here's a helpful tip for {day_name}, {date_str}!
        
        Did you know DOT Mobile rewards you with DOTM tokens for using our services? Every data purchase and subscription earns you cryptocurrency rewards that you can track right from your dashboard. These tokens are real Ethereum-based assets you can manage and use.
        
        Another powerful feature: Bitchat lets you send secure, encrypted messages to other DOT Mobile users without using any of your data allowance. It's perfect for staying connected while traveling or coordinating with fellow global citizens.
        
        Pro tip: Your eSIM profiles work seamlessly across the globe with OXIO's network infrastructure. Check your dashboard to see your current network status, manage your data usage in real-time, and access advanced features like VPN services and Wi-Fi calling.
        
        That's your tip for today - enjoy your perfectly connected experience!
        """
    
    def _generate_spanish_tip(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        return f"""
        ¡Aquí hay un consejo útil para {day_name}, {date_str}!
        
        ¿Sabías que DOT Mobile te recompensa con tokens DOTM por usar nuestros servicios? Cada compra de datos y suscripción te gana recompensas de criptomonedas que puedes rastrear desde tu panel de control. Estos tokens son activos reales basados en Ethereum.
        
        Otra característica poderosa: Bitchat te permite enviar mensajes seguros y encriptados a otros usuarios de DOT Mobile sin usar tu asignación de datos. Es perfecto para mantenerte conectado mientras viajas.
        
        Consejo profesional: Tus perfiles eSIM funcionan perfectamente en todo el mundo con la infraestructura de red de OXIO. Revisa tu panel para ver el estado de tu red, administrar tu uso de datos en tiempo real y acceder a funciones avanzadas como servicios VPN y llamadas Wi-Fi.
        
        ¡Ese es tu consejo para hoy - disfruta de tu experiencia perfectamente conectada!
        """
    
    def _generate_french_tip(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        return f"""
        Voici un conseil utile pour {day_name}, {date_str}!
        
        Saviez-vous que DOT Mobile vous récompense avec des jetons DOTM pour l'utilisation de nos services? Chaque achat de données et abonnement vous rapporte des récompenses en cryptomonnaie que vous pouvez suivre depuis votre tableau de bord. Ces jetons sont de véritables actifs basés sur Ethereum.
        
        Autre fonctionnalité puissante: Bitchat vous permet d'envoyer des messages sécurisés et cryptés à d'autres utilisateurs DOT Mobile sans utiliser votre allocation de données. C'est parfait pour rester connecté en voyage.
        
        Conseil pro: Vos profils eSIM fonctionnent parfaitement dans le monde entier avec l'infrastructure réseau d'OXIO. Consultez votre tableau de bord pour voir l'état de votre réseau, gérer votre utilisation de données en temps réel et accéder à des fonctionnalités avancées comme les services VPN et les appels Wi-Fi.
        
        C'est votre conseil pour aujourd'hui - profitez de votre expérience parfaitement connectée!
        """
    
    # UPDATE MESSAGE GENERATORS
    def _generate_english_update(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        return f"""
        Welcome back! Here's what's new on {day_name}, {date_str}.
        
        We're excited to announce some major updates to your DOT Mobile experience!
        
        First, we've launched personalized voice messages in 30 languages! You can now hear platform updates in your preferred language with your choice of 3 distinct voice profiles - CanadianRockstar for energy, ScienceTeacher for clarity, or BuddyFriend for warmth. Switch languages and voices anytime from your dashboard.
        
        We've also introduced an intelligent message system that learns as you use it. The platform now delivers progressive content - starting with welcome messages for new users, followed by helpful tips about features like DOTM token rewards and Bitchat, and finally keeping you updated with the latest platform news.
        
        Plus, our Shopify marketplace integration is now live! Browse and purchase exclusive DOT Mobile products and data packages directly from our integrated marketplace. All purchases automatically earn you DOTM token rewards.
        
        Check your dashboard to explore these new features. As always, we're working hard to keep you connected wherever you go.
        
        Thanks for being part of the DOT Mobile community!
        """
    
    def _generate_spanish_update(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        return f"""
        ¡Bienvenido de nuevo! Aquí está lo nuevo en {day_name}, {date_str}.
        
        ¡Estamos emocionados de anunciar importantes actualizaciones para tu experiencia DOT Mobile!
        
        Primero, hemos lanzado mensajes de voz personalizados en 30 idiomas. Ahora puedes escuchar actualizaciones de la plataforma en tu idioma preferido con tu elección de 3 perfiles de voz distintos - CanadianRockstar para energía, ScienceTeacher para claridad, o BuddyFriend para calidez. Cambia idiomas y voces en cualquier momento desde tu panel.
        
        También hemos introducido un sistema de mensajes inteligente que aprende mientras lo usas. La plataforma ahora entrega contenido progresivo - comenzando con mensajes de bienvenida para nuevos usuarios, seguido de consejos útiles sobre características como recompensas de tokens DOTM y Bitchat, y finalmente manteniéndote actualizado con las últimas noticias de la plataforma.
        
        Además, nuestra integración con Shopify ya está activa. Navega y compra productos exclusivos de DOT Mobile y paquetes de datos directamente desde nuestro mercado integrado. Todas las compras te ganan automáticamente recompensas de tokens DOTM.
        
        Revisa tu panel para explorar estas nuevas características. Como siempre, trabajamos duro para mantenerte conectado donde quiera que vayas.
        
        ¡Gracias por ser parte de la comunidad DOT Mobile!
        """
    
    def _generate_french_update(self, user_name, day_name, date_str, location_data=None, events_data=None, time_data=None, context_data=None):
        return f"""
        Bienvenue de retour! Voici les nouveautés du {day_name}, {date_str}.
        
        Nous sommes ravis d'annoncer des mises à jour majeures pour votre expérience DOT Mobile!
        
        Tout d'abord, nous avons lancé des messages vocaux personnalisés en 30 langues! Vous pouvez maintenant entendre les mises à jour de la plateforme dans votre langue préférée avec votre choix de 3 profils vocaux distincts - CanadianRockstar pour l'énergie, ScienceTeacher pour la clarté, ou BuddyFriend pour la chaleur. Changez de langue et de voix à tout moment depuis votre tableau de bord.
        
        Nous avons également introduit un système de messages intelligent qui apprend pendant que vous l'utilisez. La plateforme propose maintenant du contenu progressif - commençant par des messages de bienvenue pour les nouveaux utilisateurs, suivi de conseils utiles sur les fonctionnalités comme les récompenses en jetons DOTM et Bitchat, et enfin vous tenant au courant des dernières nouvelles de la plateforme.
        
        De plus, notre intégration Shopify est maintenant en ligne! Parcourez et achetez des produits exclusifs DOT Mobile et des forfaits de données directement depuis notre marketplace intégré. Tous les achats vous rapportent automatiquement des récompenses en jetons DOTM.
        
        Consultez votre tableau de bord pour explorer ces nouvelles fonctionnalités. Comme toujours, nous travaillons dur pour vous garder connecté où que vous alliez.
        
        Merci de faire partie de la communauté DOT Mobile!
        """
    
    def text_to_speech(self, text, voice_id, language="en", custom_settings=None):
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
            
            # Use custom settings if provided, otherwise use defaults
            voice_settings = custom_settings if custom_settings else {
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
