
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
    
    def generate_welcome_message(self, user_name=None, language="en", voice_profile="ScienceTeacher", message_type="welcome"):
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
        message_text = generator(user_name, day_name, date_str)
        
        return self.text_to_speech(message_text, voice_id, language, voice_settings)
    
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
    
    def _generate_german_message(self, user_name, day_name, date_str):
        name_part = f"Hallo {user_name}! Spreche ich Ihren Namen richtig aus? " if user_name else ""
        return f"{name_part}Willkommen bei DOT Mobile! Heute ist {day_name}, {date_str}, und wir freuen uns sehr, Sie in unserem globalen Konnektivitätsnetzwerk begrüßen zu dürfen. Sie sind jetzt Teil von etwas Revolutionärem - einem drahtlosen Dienst, der überall auf der Erde funktioniert. Viel Spaß beim Erkunden der Welt, während Sie perfekt verbunden bleiben!"
    
    def _generate_italian_message(self, user_name, day_name, date_str):
        name_part = f"Ciao {user_name}! Sto pronunciando correttamente il tuo nome? " if user_name else ""
        return f"{name_part}Benvenuto su DOT Mobile! Oggi è {day_name}, {date_str}, e siamo entusiasti di averti nella nostra rete di connettività globale. Sei appena diventato parte di qualcosa di rivoluzionario. Benvenuto a bordo e goditi l'esplorazione del mondo rimanendo perfettamente connesso!"
    
    def _generate_portuguese_message(self, user_name, day_name, date_str):
        name_part = f"Olá {user_name}! Estou pronunciando seu nome corretamente? " if user_name else ""
        return f"{name_part}Bem-vindo ao DOT Mobile! Hoje é {day_name}, {date_str}, e estamos emocionados por você se juntar à nossa rede de conectividade global. Você acabou de fazer parte de algo revolucionário. Bem-vindo a bordo e aproveite explorando o mundo enquanto permanece perfeitamente conectado!"
    
    def _generate_dutch_message(self, user_name, day_name, date_str):
        name_part = f"Hallo {user_name}! Spreek ik uw naam correct uit? " if user_name else ""
        return f"{name_part}Welkom bij DOT Mobile! Vandaag is het {day_name}, {date_str}, en we zijn verheugd om u te verwelkomen in ons wereldwijde connectiviteitsnetwerk. U bent nu deel van iets revolutionairs. Welkom aan boord en geniet van het verkennen van de wereld terwijl u perfect verbonden blijft!"
    
    def _generate_polish_message(self, user_name, day_name, date_str):
        name_part = f"Cześć {user_name}! Czy poprawnie wymawiam twoje imię? " if user_name else ""
        return f"{name_part}Witamy w DOT Mobile! Dzisiaj jest {day_name}, {date_str}, i jesteśmy podekscytowani, że dołączasz do naszej globalnej sieci łączności. Właśnie stałeś się częścią czegoś rewolucyjnego. Witamy na pokładzie i ciesz się odkrywaniem świata, pozostając doskonale połączonym!"
    
    def _generate_arabic_message(self, user_name, day_name, date_str):
        name_part = f"مرحباً {user_name}! هل أنطق اسمك بشكل صحيح؟ " if user_name else ""
        return f"{name_part}مرحباً بك في DOT Mobile! اليوم هو {day_name}، {date_str}، ونحن متحمسون لانضمامك إلى شبكة الاتصال العالمية لدينا. لقد أصبحت جزءاً من شيء ثوري. مرحباً بك على متن الطائرة واستمتع باستكشاف العالم أثناء البقاء متصلاً بشكل مثالي!"
    
    def _generate_hindi_message(self, user_name, day_name, date_str):
        name_part = f"नमस्ते {user_name}! क्या मैं आपका नाम सही से बोल रहा हूं? " if user_name else ""
        return f"{name_part}DOT Mobile में आपका स्वागत है! आज {day_name}, {date_str} है, और हम आपको हमारे वैश्विक कनेक्टिविटी नेटवर्क में शामिल होने के लिए रोमांचित हैं। आप कुछ क्रांतिकारी का हिस्सा बन गए हैं। स्वागत है और पूरी तरह से जुड़े रहते हुए दुनिया की खोज का आनंद लें!"
    
    def _generate_japanese_message(self, user_name, day_name, date_str):
        name_part = f"こんにちは{user_name}さん！お名前の発音は正しいですか？ " if user_name else ""
        return f"{name_part}DOT Mobileへようこそ！今日は{day_name}、{date_str}です。グローバル接続ネットワークへの参加を歓迎します。あなたは革命的な何かの一部になりました。ようこそ、完璧に接続されたまま世界を探索することをお楽しみください！"
    
    def _generate_korean_message(self, user_name, day_name, date_str):
        name_part = f"안녕하세요 {user_name}님! 제가 이름을 올바르게 발음하고 있나요? " if user_name else ""
        return f"{name_part}DOT Mobile에 오신 것을 환영합니다! 오늘은 {day_name}, {date_str}입니다. 글로벌 연결 네트워크에 참여하게 되어 기쁩니다. 당신은 혁명적인 무언가의 일부가 되었습니다. 환영합니다. 완벽하게 연결된 상태에서 세계를 탐험하는 것을 즐기십시오!"
    
    def _generate_chinese_message(self, user_name, day_name, date_str):
        name_part = f"你好{user_name}！我的发音正确吗？ " if user_name else ""
        return f"{name_part}欢迎来到DOT Mobile！今天是{day_name}，{date_str}，我们很高兴您加入我们的全球连接网络。您刚刚成为革命性事物的一部分。欢迎加入，享受在保持完美连接的同时探索世界！"
    
    def _generate_russian_message(self, user_name, day_name, date_str):
        name_part = f"Здравствуйте {user_name}! Я правильно произношу ваше имя? " if user_name else ""
        return f"{name_part}Добро пожаловать в DOT Mobile! Сегодня {day_name}, {date_str}, и мы рады приветствовать вас в нашей глобальной сети подключения. Вы только что стали частью чего-то революционного. Добро пожаловать на борт и наслаждайтесь исследованием мира, оставаясь идеально подключенными!"
    
    def _generate_turkish_message(self, user_name, day_name, date_str):
        name_part = f"Merhaba {user_name}! Adınızı doğru telaffuz ediyor muyum? " if user_name else ""
        return f"{name_part}DOT Mobile'a hoş geldiniz! Bugün {day_name}, {date_str} ve küresel bağlantı ağımıza katılmanızdan heyecan duyuyoruz. Devrimci bir şeyin parçası oldunuz. Hoş geldiniz ve mükemmel şekilde bağlı kalırken dünyayı keşfetmenin tadını çıkarın!"
    
    def _generate_swedish_message(self, user_name, day_name, date_str):
        name_part = f"Hej {user_name}! Uttalar jag ditt namn korrekt? " if user_name else ""
        return f"{name_part}Välkommen till DOT Mobile! Idag är det {day_name}, {date_str}, och vi är glada att välkomna dig till vårt globala anslutningsnätverk. Du har precis blivit en del av något revolutionerande. Välkommen ombord och njut av att utforska världen samtidigt som du förblir perfekt ansluten!"
    
    def _generate_norwegian_message(self, user_name, day_name, date_str):
        name_part = f"Hei {user_name}! Uttaler jeg navnet ditt riktig? " if user_name else ""
        return f"{name_part}Velkommen til DOT Mobile! I dag er det {day_name}, {date_str}, og vi er glade for å ønske deg velkommen til vårt globale tilkoblingsnettverk. Du har nettopp blitt en del av noe revolusjonerende. Velkommen om bord og nyt å utforske verden mens du forblir perfekt tilkoblet!"
    
    def _generate_danish_message(self, user_name, day_name, date_str):
        name_part = f"Hej {user_name}! Udtaler jeg dit navn korrekt? " if user_name else ""
        return f"{name_part}Velkommen til DOT Mobile! I dag er det {day_name}, {date_str}, og vi er glade for at byde dig velkommen til vores globale forbindelsesnetværk. Du er lige blevet en del af noget revolutionerende. Velkommen ombord og nyd at udforske verden, mens du forbliver perfekt forbundet!"
    
    def _generate_finnish_message(self, user_name, day_name, date_str):
        name_part = f"Hei {user_name}! Äänänkö nimesi oikein? " if user_name else ""
        return f"{name_part}Tervetuloa DOT Mobileen! Tänään on {day_name}, {date_str}, ja olemme innoissamme toivottaessamme sinut tervetulleeksi maailmanlaajuiseen yhteysverkostoomme. Olet juuri tullut osaksi jotain vallankumouksellista. Tervetuloa kyytiin ja nauti maailman tutkimisesta pysyen täydellisesti yhteydessä!"
    
    def _generate_czech_message(self, user_name, day_name, date_str):
        name_part = f"Ahoj {user_name}! Vyslovuji tvoje jméno správně? " if user_name else ""
        return f"{name_part}Vítejte v DOT Mobile! Dnes je {day_name}, {date_str}, a jsme rádi, že vás můžeme přivítat v naší globální síti připojení. Právě jste se stali součástí něčeho revolučního. Vítejte na palubě a užijte si zkoumání světa, zatímco zůstanete dokonale připojeni!"
    
    def _generate_romanian_message(self, user_name, day_name, date_str):
        name_part = f"Bună {user_name}! Pronunț corect numele tău? " if user_name else ""
        return f"{name_part}Bun venit la DOT Mobile! Astăzi este {day_name}, {date_str}, și suntem încântați să vă primim în rețeaua noastră globală de conectivitate. Tocmai ați devenit parte dintr-un lucru revoluționar. Bun venit la bord și bucurați-vă de explorarea lumii rămânând perfect conectat!"
    
    def _generate_greek_message(self, user_name, day_name, date_str):
        name_part = f"Γεια σου {user_name}! Προφέρω σωστά το όνομά σου; " if user_name else ""
        return f"{name_part}Καλώς ήρθατε στο DOT Mobile! Σήμερα είναι {day_name}, {date_str}, και είμαστε ενθουσιασμένοι που σας καλωσορίζουμε στο παγκόσμιο δίκτυο συνδεσιμότητάς μας. Μόλις γίνατε μέρος κάτι επαναστατικού. Καλώς ήρθατε και απολαύστε την εξερεύνηση του κόσμου ενώ παραμένετε τέλεια συνδεδεμένοι!"
    
    def _generate_hebrew_message(self, user_name, day_name, date_str):
        name_part = f"שלום {user_name}! האם אני מבטא את שמך נכון? " if user_name else ""
        return f"{name_part}ברוכים הבאים ל-DOT Mobile! היום הוא {day_name}, {date_str}, ואנחנו נרגשים לקבל אתכם לרשת הקישוריות הגלובלית שלנו. הרגע הפכתם לחלק ממשהו מהפכני. ברוכים הבאים ותהנו לחקור את העולם תוך שמירה על חיבור מושלם!"
    
    def _generate_thai_message(self, user_name, day_name, date_str):
        name_part = f"สวัสดี {user_name}! ฉันออกเสียงชื่อคุณถูกต้องไหม? " if user_name else ""
        return f"{name_part}ยินดีต้อนรับสู่ DOT Mobile! วันนี้คือ {day_name}, {date_str} และเรายินดีที่จะต้อนรับคุณเข้าสู่เครือข่ายการเชื่อมต่อทั่วโลกของเรา คุณเพิ่งกลายเป็นส่วนหนึ่งของบางสิ่งที่ปฏิวัติ ยินดีต้อนรับและสนุกกับการสำรวจโลกในขณะที่เชื่อมต่ออย่างสมบูรณ์แบบ!"
    
    def _generate_vietnamese_message(self, user_name, day_name, date_str):
        name_part = f"Xin chào {user_name}! Tôi có phát âm tên của bạn đúng không? " if user_name else ""
        return f"{name_part}Chào mừng đến với DOT Mobile! Hôm nay là {day_name}, {date_str}, và chúng tôi rất vui mừng chào đón bạn vào mạng kết nối toàn cầu của chúng tôi. Bạn vừa trở thành một phần của điều gì đó mang tính cách mạng. Chào mừng và tận hưởng việc khám phá thế giới trong khi vẫn kết nối hoàn hảo!"
    
    def _generate_indonesian_message(self, user_name, day_name, date_str):
        name_part = f"Halo {user_name}! Apakah saya mengucapkan nama Anda dengan benar? " if user_name else ""
        return f"{name_part}Selamat datang di DOT Mobile! Hari ini adalah {day_name}, {date_str}, dan kami senang menyambut Anda ke jaringan konektivitas global kami. Anda baru saja menjadi bagian dari sesuatu yang revolusioner. Selamat datang dan nikmati menjelajahi dunia sambil tetap terhubung dengan sempurna!"
    
    def _generate_malay_message(self, user_name, day_name, date_str):
        name_part = f"Halo {user_name}! Adakah saya menyebut nama anda dengan betul? " if user_name else ""
        return f"{name_part}Selamat datang ke DOT Mobile! Hari ini ialah {day_name}, {date_str}, dan kami teruja untuk mengalu-alukan anda ke rangkaian sambungan global kami. Anda baru sahaja menjadi sebahagian daripada sesuatu yang revolusioner. Selamat datang dan nikmatilah meneroka dunia sambil kekal bersambung dengan sempurna!"
    
    def _generate_filipino_message(self, user_name, day_name, date_str):
        name_part = f"Kamusta {user_name}! Tama ba ang pagbigkas ko sa iyong pangalan? " if user_name else ""
        return f"{name_part}Maligayang pagdating sa DOT Mobile! Ngayong araw ay {day_name}, {date_str}, at nasasabik kaming tanggapin ka sa aming pandaigdigang network ng koneksyon. Ikaw ay naging bahagi ng isang rebolusyonaryong bagay. Maligayang pagdating at tamasahin ang paggalugad sa mundo habang nananatiling perpektong konektado!"
    
    def _generate_ukrainian_message(self, user_name, day_name, date_str):
        name_part = f"Привіт {user_name}! Чи правильно я вимовляю ваше ім'я? " if user_name else ""
        return f"{name_part}Ласкаво просимо до DOT Mobile! Сьогодні {day_name}, {date_str}, і ми раді вітати вас у нашій глобальній мережі зв'язку. Ви щойно стали частиною чогось революційного. Ласкаво просимо і насолоджуйтесь дослідженням світу, залишаючись ідеально підключеними!"
    
    def _generate_bulgarian_message(self, user_name, day_name, date_str):
        name_part = f"Здравей {user_name}! Произнасям ли правилно името ти? " if user_name else ""
        return f"{name_part}Добре дошли в DOT Mobile! Днес е {day_name}, {date_str}, и сме развълнувани да ви приветстваме в нашата глобална мрежа за свързаност. Току-що станахте част от нещо революционно. Добре дошли и се насладете на изследването на света, докато оставате перфектно свързани!"
    
    # TIP MESSAGE GENERATORS
    def _generate_english_tip(self, user_name, day_name, date_str):
        return f"""
        Here's a quick tip for today, {day_name}, {date_str}!
        
        Did you know you can easily manage your data usage right from your dashboard? Simply tap on the data circle to see a detailed breakdown of your consumption patterns.
        
        To get the most out of your global connectivity, we recommend enabling automatic eSIM profile switching in your settings. This ensures you're always on the best network wherever you travel.
        
        Don't forget to check out our marketplace for exclusive data deals and packages. You can also earn DOTM tokens by referring friends - each successful referral gives you bonus tokens to use across our platform.
        
        Pro tip: Use the Bitchat feature to stay connected with other DOT Mobile users without using your data allowance. It's perfect for coordinating with travel companions or networking with other global citizens.
        
        That's your tip for today - enjoy your perfectly connected experience!
        """
    
    def _generate_spanish_tip(self, user_name, day_name, date_str):
        return f"""
        ¡Aquí hay un consejo rápido para hoy, {day_name}, {date_str}!
        
        ¿Sabías que puedes administrar fácilmente tu uso de datos desde tu panel de control? Simplemente toca el círculo de datos para ver un desglose detallado de tus patrones de consumo.
        
        Para aprovechar al máximo tu conectividad global, recomendamos habilitar el cambio automático de perfil eSIM en tu configuración.
        
        ¡Ese es tu consejo para hoy - disfruta de tu experiencia perfectamente conectada!
        """
    
    def _generate_french_tip(self, user_name, day_name, date_str):
        return f"""
        Voici un conseil rapide pour aujourd'hui, {day_name}, {date_str}!
        
        Saviez-vous que vous pouvez facilement gérer votre utilisation de données depuis votre tableau de bord? Appuyez simplement sur le cercle de données pour voir une répartition détaillée de vos modèles de consommation.
        
        Pour tirer le meilleur parti de votre connectivité mondiale, nous recommandons d'activer le changement automatique de profil eSIM dans vos paramètres.
        
        C'est votre conseil pour aujourd'hui - profitez de votre expérience parfaitement connectée!
        """
    
    # UPDATE MESSAGE GENERATORS
    def _generate_english_update(self, user_name, day_name, date_str):
        return f"""
        Welcome back! Here's what's new on {day_name}, {date_str}.
        
        We're excited to announce some fresh updates to your DOT Mobile experience!
        
        First, we've launched our new Encrypted Bluetooth Mesh Network feature. You can now connect with nearby DOT Mobile users to create a secure, decentralized communication network. Check it out in your dashboard!
        
        We've also enhanced our global coverage with new partnerships in Southeast Asia and Latin America. This means even better connectivity and more affordable rates in over 25 new countries.
        
        Your DOTM token rewards program has been upgraded! You can now use tokens for premium features like priority customer support, exclusive data packages, and early access to new services.
        
        Don't forget to update your app to the latest version to enjoy all these new features. As always, we're working hard to keep you connected wherever you go.
        
        Thanks for being part of the DOT Mobile community!
        """
    
    def _generate_spanish_update(self, user_name, day_name, date_str):
        return f"""
        ¡Bienvenido de nuevo! Aquí está lo nuevo en {day_name}, {date_str}.
        
        ¡Estamos emocionados de anunciar algunas actualizaciones nuevas para tu experiencia DOT Mobile!
        
        Primero, hemos lanzado nuestra nueva función de Red Mesh Bluetooth Encriptada. Ahora puedes conectarte con usuarios cercanos de DOT Mobile para crear una red de comunicación segura y descentralizada.
        
        ¡Gracias por ser parte de la comunidad DOT Mobile!
        """
    
    def _generate_french_update(self, user_name, day_name, date_str):
        return f"""
        Bienvenue de retour! Voici les nouveautés du {day_name}, {date_str}.
        
        Nous sommes ravis d'annoncer de nouvelles mises à jour pour votre expérience DOT Mobile!
        
        Tout d'abord, nous avons lancé notre nouvelle fonctionnalité de Réseau Maillé Bluetooth Crypté. Vous pouvez maintenant vous connecter avec les utilisateurs DOT Mobile à proximité pour créer un réseau de communication sécurisé et décentralisé.
        
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
