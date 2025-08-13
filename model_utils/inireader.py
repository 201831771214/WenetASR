import configparser
import ast

INI_PATH="./configs/cfg.ini"

class IniReader:
    def __init__(self, ini_path:str = INI_PATH, inline_comment_prefixes:str = ";", encoding:str="utf-8"):
        self.ini_path = ini_path
        self.cfgparser = None
        self.inline_comment_prefixes = inline_comment_prefixes
        self.encoding = encoding
        self.sections = []
        
        self.cfg = {}
        
        self.__InitCFG()
    
    def __InitCFG(self):
        self.cfgparser = configparser.ConfigParser(inline_comment_prefixes=self.inline_comment_prefixes)
        self.cfgparser.read(self.ini_path, encoding=self.encoding)
        
        self.sections = self.cfgparser.sections()
    
    def GetConfig(self) -> dict:
        self.cfgparser.read(self.ini_path, encoding=self.encoding)
        for section in self.sections:
            for key in self.cfgparser[section]:
                value = self.cfgparser.get(section, key)
                self.cfg[key] = self._parse_value(value)
        
        return self.cfg
    
    def _parse_value(self, value: str):
        """智能解析配置值"""
        if not value:
            return value
        
        # 尝试使用 ast.literal_eval 解析 Python 字面量
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # 如果解析失败，尝试其他解析方法
            pass
        
        # 尝试解析布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 尝试解析数字
        try:
            # 尝试解析整数
            if '.' not in value and 'e' not in value.lower():
                return int(value)
            else:
                # 尝试解析浮点数
                return float(value)
        except ValueError:
            pass
        
        # 如果都失败了，返回原始字符串
        return value
    
    def GetValueByKey(self, section:str, key:str):
        if section in self.sections:
            return self.cfgparser.get(section, key)
        else:
            return None
        
    def UpdateValueByKey(self, section:str, key:str, value:str) -> bool:
        if section in self.sections:
            self.cfgparser.set(section, key, value)
            with open(self.ini_path, "w", encoding="utf-8") as f:
                self.cfgparser.write(f)
            return True
        else:
            return False