class TranslationDict:
    def __init__(self, languages=['zh', 'en']):
        self.languages = languages
        self.text_dict = {lang: {} for lang in languages}

    def add_text(self, key, texts):
        """
        添加翻译文本
        :param key: 翻译键
        :param texts: 一个字典或列表,包含每种语言对应的文本
        """
        if isinstance(texts, dict):
            for lang, text in texts.items():
                if lang in self.languages:
                    self.text_dict[lang][key] = text
        elif isinstance(texts, list):
            textlength=len(texts)
            languagelength=len(self.languages)
            if languagelength>textlength:
                print(f'{key}存在没有翻译的语言，设置为空字符，相关语种：',self.languages[textlength:])
                text_list+=['' for x in range(languagelength-textlength)]
            elif languagelength<textlength:
                print(f'{key}的翻译存在未定义的语种，设置为新语言，相关文本：',textinfo[languagelength:])
                for x in range(textlength-languagelength):
                    self.languages+=[f'lang{x}']
                    self.text_dict[f'lang{x}'] = {}
            for lang, text in zip(self.languages, texts):
                self.text_dict[lang][key] = text

    def generate_translation_list_from_df(self,df,dfcolumn_key,finaldict_key,origin_list=None,base_key='en',bIgnoreBlank=False):
        target_language_column_name=self.get_text(dfcolumn_key,base_key)
        if origin_list is None:#不传列表就是默认映射
            origin_list=sorted(df[target_language_column_name].unique().tolist())
            if bIgnoreBlank:
                if origin_list[0]=='':
                    origin_list.pop(0)            
        if base_key=='en':
            another_key='zh'
        else:
            another_key='en'
        idx_map = dict(zip(df[target_language_column_name], df.index))
        #如果要中英都支持，这里就要做一个映射
        another_list=[]
        anather_column=self.get_text(dfcolumn_key,another_key)
        for name in origin_list:
            if name in idx_map:
                another_list.append(df.loc[idx_map[name], anather_column])
            else:
                another_list.append(name)
        if base_key=='en':
            result=[another_list, origin_list]
        else:
            result=[origin_list, another_list]
        self.add_text(finaldict_key,result)
    def get_text(self, key, language='zh'):
        """
        获取指定语言的翻译文本
        :param key: 翻译键
        :param language: 语言标识符
        :return: 翻译文本,如果不存在则返回None
        """
        return self.text_dict.get(language, {}).get(key, None)

    def get_dict(self):
        """
        获取当前的翻译字典
        :return: 翻译字典
        """
        return self.text_dict
    def get_language_dict(self, language='zh'):
        """
        获取置顶语言的翻译字典
        :param language: 语言标识符
        :return: 翻译字典
        """
        return self.text_dict.get(language, {})