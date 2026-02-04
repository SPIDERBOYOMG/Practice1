#class_variables.py
class Dictionary:
    default_language = "English"
    default_country = "USA"

    def __init__(self, language=None, country=None):
        self.language = language if language else Dictionary.default_language
        self.country = country if country else Dictionary.default_country

    def info(self):
        return f"Language: {self.language}, Country: {self.country}"
d1 = Dictionary()
d2 = Dictionary(language="Spanish", country="Spain")
print(d1.info())
print(d2.info())
# End of class_variables.py
