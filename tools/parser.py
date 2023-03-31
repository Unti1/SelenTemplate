from settings import *

class InstPars():#Thread):
    def __init__(self, profile_id: str, invisable=False) -> None:
        """Шаблон для парсера с антидетект браузером Dolphin Anty

        Args:
            profile_id (str, optional): профиль ID от бразуера.
            invisable (bool, optional): запуск в свернутом режиме. Defaults to False.
            Версии эмуляторов: https://anty.dolphin.ru.com/docs/basic-automation/
            Для Linux сделать предвартилеьно chmo+x ..utils/cromedriver-linux
        """
        self.browser_startUp(profile_id,invisable = invisable)
        

    def browser_startUp(self, PROFILE_ID,invisable):
        """Создание настройка и создания эмуляции браузера
        """ 
        options = webdriver.ChromeOptions()
        match platform.system():
            case "Windows":
                if platform.architecture() == "64bit":
                    chrome_drive_path = Service('/utils/chromedriver-win-x64')
                else: 
                    chrome_drive_path = Service('/utils/chromedriver-win-x86')
            case "Linux":
                chrome_drive_path = Service('./utils/chromedriver-linux')
                options.add_argument('--no-sandbox')
            case "Darwin":
                if platform.architecture() == "m1":
                    chrome_drive_path = Service('./utils/chromedriver-mac-m1')
                else:
                    chrome_drive_path = Service('./utils/chromedriver-mac-intel')


        response = requests.get(f'http://localhost:3001/v1.0/browser_profiles/{PROFILE_ID}/start?automation=1')
        respons_json = response.json()
        options.debugger_address = f"127.0.0.1:{respons_json['automation']['port']}"
        if invisable:
            options.add_argument('--headless')
        self.driver = webdriver.Chrome(service=chrome_drive_path,chrome_options=options)
