from datetime import datetime

def date_time():
        date = datetime.now()
        return date.strftime("%d/%m/%Y %H:%M:%S")
