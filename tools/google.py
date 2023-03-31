from settings import *

# TODO: Переработать
class GoogleService(Thread):

    def __init__(self):
        # Настройки потоков
        # super(GoogleService, self).__init__()
        # Thread.__init__(self)

        self.spreadsheet_id = config["Google"]["table_id"]
        # Настройки таблицы
        self.creds = None
        self.creditions_check()
        self.service = build('sheets', 'v4', credentials=self.creds)
        # Объект данных
        # Сохраняем отдельным объектом базу данных
        self.table_data = self.formating_to_dict(self.get_all_values_db())
        self.instagram_acc_len = 0
        # При запуске работать постоянно(пока не будет передано False)
        self.running = True

    def get_all_values_db(self, range_names="Лист1!A:F"):
        try:
            range_names = range_names
            result = self.service.spreadsheets().values().batchGet(
                spreadsheetId=self.spreadsheet_id, ranges=range_names).execute()
            ranges = result.get('valueRanges', [])
            # logging.info(f"{len(ranges)} ranges retrieved")
            result = result.get('valueRanges')[0].get('values')
            return result
        except HttpError as error:
            logging.error(f"An error occurred: {error}")
            return error


##################################################################################################

    def telegram_channels(self, range_names="Лист1!A:W"):
        spreadsheet_id = config["Telegram"]["table_id"]
        try:
            range_names = range_names
            result = self.service.spreadsheets().values().batchGet(
                spreadsheetId=spreadsheet_id, ranges=range_names).execute()
            ranges = result.get('valueRanges', [])
            # logging.info(f"{len(ranges)} ranges retrieved")
            result = result.get('valueRanges')[0].get('values')
            result = sum(result,[])
            result = list(set(filter(lambda x: x !="",result)))
            return result
        except HttpError as error:
            logging.error(f"An error occurred: {error}")
            return error

    def instagram_accounts(self,range_names="Лист1!A:W"):
        """ Выгружает инстаграм аккаунты с гугл таблицы

        Returns:
            list[list]: Каждый аккаунт в формате [["данные","количество выполненных действий","дата последнего работы"]] 
        """
        spreadsheet_id = config["Instagram"]["table_id"]
        try:
            range_names = range_names
            result = self.service.spreadsheets().values().batchGet(
                spreadsheetId=spreadsheet_id, ranges=range_names).execute()
            ranges = result.get('valueRanges', [])
            # logging.info(f"{len(ranges)} ranges retrieved")
            result = result.get('valueRanges')[0].get('values')[1:]
            self.instagram_acc_len = len(result) # обновление количества аккаунтов
            return result
        except HttpError as error:
            logging.error(f"An error occurred: {error}")
            return error

    def check_account_limit(self,data):
        if len(data) > 5:
            date = data[2]
            count = int(data[1])
            if type(date) == str and date != '':
                date = datetime.datetime.strptime(date,"%Y-%m-%d %H:%M")
            else:
                return False
            day_left = (datetime.datetime.timestamp(datetime.datetime.now()) - datetime.datetime.timestamp(date))/86400
        
            if day_left >= 1:
                return(True)
            elif count < int(config["Instagram"]["total_actions"]):
                return(True)
        return False

    def inst_find_value(self, value, column):
        try:
            spreadsheet_id = config["Instagram"]["table_id"]
            column_translate = {1: "A:A", 2: "B:B", 3: "C:C", 4: "D:D",
                                5: "E:E", 6: "F:F", 7: "G:G", 8: "H:H", 9: "I:I"}
            rangeName = f"Лист1!{column_translate[column]}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=rangeName).execute()
            values = result.get('values', [])
            for i in range(len(values)):
                if values[i] != []:
                    if values[i][0] == value:
                        return i + 1
            return None
        except Exception as e:
            logging.error(e)

    def instagram_update_values(self, search_value: str, value: list):
        '''
        Аргументы
        1 - значение - поиск в таблице по написанию
        2 - список замены (с первым параметром по которому искали)
        '''
        spreadsheet_id = config["Instagram"]["table_id"]
        if len(value) < 2:
            return
        try:
            ind = self.inst_find_value(search_value, 1)
            if ind == None:
                return

            range_name = f"Лист1!A{ind}:F{ind}"
            data = [
                {
                    'range': range_name,
                    'values': [value]
                },
                # Additional ranges to update ...
            ]
            body = {
                'valueInputOption': "USER_ENTERED",
                'data': data
            }

            result = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()
            # logging.info(f"{(result)} cells updated.")
            return result
        except HttpError as error:
            logging.error(f"An error occurred: {error}")
            return error
##################################################################################################
    
    def formating_to_dict(self, data: list):
        dct = {}
        if data:
            for dat in data:
                if len(dat) > 1:
                    dct[dat[0]] = dat[1:]
        return (dct)

    def append_db(self, value: list[str], range_names="Лист1!A:A"):
        if len(value) < 2:
            return
        try:
            if value[0] in self.table_data.keys():# Если есть, просто обновляем
                logging.info(f"{value[0]} аккаунт уже добавлен")
                if value[1:] == self.table_data[value[0]]:# ...если конечно есть на то причины
                    return
                else:
                    return(self.update_values(value[0],value))

            resource = {
                "majorDimension": "ROWS",
                "values": [value]
            }
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_names,
                body=resource,
                valueInputOption="USER_ENTERED"
            ).execute()
            self.table_data[value[0]] = value[1:]
            return (result)
        except HttpError as error:
            logging.error(f"An error occurred: {error}")
            return error

    def creditions_check(self):
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/gmail.readonly']
        if os.path.exists('settings/token.json'):
            self.creds = Credentials.from_authorized_user_file(
                'settings/token.json', SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'settings/credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('settings/token.json', 'w') as token:
                token.write(self.creds.to_json())

    def create_db(self):
        try:
            spreadsheet = {
                'properties': {
                    'title': input("Entery Table name: ")
                }
            }
            spreadsheet = self.service.spreadsheets().create(body=spreadsheet,
                                                             fields='spreadsheetId') \
                .execute()
            logging.info(
                f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
            print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
            return spreadsheet.get('spreadsheetId')
        except HttpError as error:
            logging.error(f"An error occurred: {error}")
            return error

    def update_values(self, search_value: str, value: list):
        '''
        Аргументы
        1 - значение - поиск в таблице по написнию
        2 - список замены (с первым параметром по которому искали)
        '''
        if len(value) < 2:
            return
        try:
            ind = self.find_value_in_col(search_value, 1)
            if ind == None:
                return (self.append_db(value))

            range_name = f"Лист1!A{ind}:F{ind}"

            data = [
                {
                    'range': range_name,
                    'values': [value]
                },
                # Additional ranges to update ...
            ]
            body = {
                'valueInputOption': "USER_ENTERED",
                'data': data
            }
            result = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id, body=body).execute()
            logging.info(f"{(result)} cells updated.")
            self.table_data[value[0]] = value[1:]
            return result
        except HttpError as error:
            logging.error(f"An error occurred: {error}")
            return error

    def find_value_in_col(self, value, column):
        try:
            column_translate = {1: "A:A", 2: "B:B", 3: "C:C", 4: "D:D",
                                5: "E:E", 6: "F:F", 7: "G:G", 8: "H:H", 9: "I:I"}
            rangeName = f"Лист1!{column_translate[column]}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range=rangeName).execute()
            values = result.get('values', [])
            for i in range(len(values)):
                if values[i] != []:
                    if values[i][0] == value:
                        return i + 1
            return None
        except Exception as e:
            logging.error(e)

    def get_mail_code(self):
        counter = 0
        while counter < int(config["Google"]["max_try"]):
            time.sleep(float(config["Google"]["code_wait"]))
            try:
                # Call the Gmail API
                service = build('gmail', 'v1', credentials=self.creds)
                results = service.users().messages().list(userId='me').execute()
                messages_id = results.get('messages', [])
                for id in list(map(lambda x: x.get('id'), messages_id)):
                    msg = service.users().messages().get(userId='me', id=id).execute()

                    date_in_sec = int(msg.get('internalDate'))/1000
                    last = datetime.datetime.timestamp(
                        datetime.datetime.now() - datetime.timedelta(hours=1))
                    past = datetime.datetime.timestamp(
                        datetime.datetime.now() + datetime.timedelta(hours=1))

                    msg = msg.get('snippet')
                    code = re.search(r"\d{6}", msg)
                    if code and (date_in_sec in range(int(last), int(past))):
                        logging.info("Код получен")
                        return (code[0])

            except HttpError as error:
                # TODO(developer) - Handle errors from gmail API.
                logging.error(f'An error occurred: {error}')
            counter += 1
        else:
            logging.error(
                f"Спустя {config['Google']['max_try']} попыток, не удалось дождаться сообщения на почте")

    def run(self):
        try:
            while self.running:
                time.sleep(float(config["Google"]["service_sleep"]))
            else:
                print("Взаимодействие с Google Сервисами завершено")
        except:
            self.running = False
            logging.error(traceback.format_exc())


if __name__ == "__main__":
    # GoogleService().get_mail_code()
    # print(GoogleService().telegram_channels())
    # GoogleService().append_db(["Имя6","Цена там","Что то еще"])
    # GoogleService().create_db()
    # GoogleService().find_value_in_col("A", 1)
    # GoogleService().update_values("A", ["A23", "B23"])
    pass
