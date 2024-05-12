#依赖库和不怎么常修改的函数部分
import pandas as pd
import numpy as np
import solara
from solara import reactive
from solara.alias import rv
from Module import Common
import re
import pypinyin
from typing import Any, Dict, Optional, cast

def get_pinyin_with_char(text):
    pinyins = pypinyin.lazy_pinyin(text, style=pypinyin.NORMAL)
    result = []
    for char, pinyin in zip(text, pinyins):
        result.append(char + pinyin)
    return ' '.join(result)
    
def add_pinyin_column(df, column_name,new_column_name='pinyin'):
    df[new_column_name] = df[column_name].apply(get_pinyin_with_char)
    return df

def is_pure_chinese(text):
    chinese_pattern = r'^[\u4e00-\u9fa5]+$'
    return bool(re.match(chinese_pattern, text))

def ApplyFilter_Regex(args,df,filter_column='名称',filter_column_pinyin='pinyin'):#待修改
    # namelabel=translation_dict.get_text('dfname_Itemname',language.value)#这里还是区分一下中英文，而不是混合匹配
    
    # is_chinese = all(pypinyin.pinyin(char, style=pypinyin.NORMAL) for char in args)
    is_chinese = is_pure_chinese(args)

    # 构建正则表达式模式
    pattern = '.*'.join(re.escape(char) for char in args)
    regex = re.compile(pattern, re.IGNORECASE)
    # print(pattern,regex,is_chinese)

    if (language.value=='en')or(is_chinese):
        newdf = df[df[filter_column].str.contains(regex, na=False, regex=True)].copy()
        matched_additional_values = [val for val in additional_values if regex.search(val)]#这里也要传参？英语怎么办？互斥的。记得验收一下
    else:
        newdf = df[df[filter_column_pinyin].str.contains(regex, na=False, regex=True)].copy()
        matched_additional_values = [val for val in additional_values_pinyin if regex.search(val)]#这里也要传参？
        
    unique_items = sorted(newdf[filter_column].unique().tolist())
    
    itemlist_new=matched_additional_values+unique_items#调整顺序，前面的在前面
    return itemlist_new    


def change_language(args):#可以公共引用的函数就拿出来 #待修改，处理道具列表
    global item_dict
    if language_Lable.value=='中文':
        language.value='zh'
    elif language_Lable.value=='English':
        language.value='en'
    #更换依赖的dict会导致多选组件出错，所以最好的做法就是先清空组件选项，然后再赋值
    
    #缓存多选的值，更换后再取回来，其他几个选项也要这么处理。
    gateitem_selection=unlock_items.value.copy()
    gateitem_list=language_dict.value.get('dfname_UnlockList').copy()
    gateindices = [gateitem_list.index(item) for item in gateitem_selection if item in gateitem_list]

    heronamelist=language_dict.value.get('dfname_HeroList').copy()
    heroindice=heronamelist.index(hero.value)

    badge_selection=hero_badge.value.copy()
    badge_list=language_dict.value.get('dfname_SubClassList').copy()
    badgeindices = [badge_list.index(item) for item in badge_selection if item in badge_list]

    raritylist=language_dict.value.get('dfname_RarityList').copy()
    rarityindice=raritylist.index(rarity.value)

    unlock_items.value=[]
    hero_badge.value=[]
    
    language_dict.value=translation_dict.get_language_dict(language.value)#文本字典库
    unlock_items.value=[language_dict.value.get('dfname_UnlockList')[pos] for pos in gateindices]
    hero.value=language_dict.value.get('dfname_HeroList')[heroindice]
    hero_badge.value=[language_dict.value.get('dfname_SubClassList')[pos] for pos in badgeindices]
    rarity.value=language_dict.value.get('dfname_RarityList')[rarityindice]
    return
    
def generate_actual_rate(gameround=1,class_selected='',ignorefilter='',unlock_selected=[''],other_class_activated=[],rarity_selected='all',locked_num=0,debugmode=False,autoupdate=True):
#这个函数依赖后面定义的全局变量
    df_cl_ItemName=language_dict.value.get('dfname_Itemname')
    df_cl_Clase=language_dict.value.get('dfname_Classname')
    df_cl_Chance=language_dict.value.get('dfname_Chancename')
    df_cl_Rarity=language_dict.value.get('dfname_Rarityname')
    df_cl_value=language_dict.value.get('dfname_valuename')
    rt_filter_type=default_filter_column.value
    beginline=93
    if (gameround<1)or(gameround>18):
        gameround=min(max(1,gameround),18)
        print(f'回合数超过上限，设置回最接近的{gameround}')
    final_item=dfitem.copy()
    if debugmode:
        print(f'line{beginline+6}',final_item.shape[0])
    final_item=final_item[final_item['物品来源']=='商店']
    if debugmode:
        print(f'line{beginline+9}',final_item.shape[0],list(final_item[df_cl_ItemName]))    
    if class_selected!='':
        if not(language_dict.value.get('badge_rainbow') in other_class_activated):#彩虹刷所有道具
            if language_dict.value.get('badge_stone') in other_class_activated:
                final_item=final_item[~(final_item[df_cl_Clase]==class_selected)]
            final_item=final_item[((final_item[df_cl_Clase]=='')|(final_item[df_cl_Clase]==class_selected)|(final_item[df_cl_Clase].isin(other_class_activated)))]
        if debugmode:
            print(f'line{beginline+16}',final_item.shape[0],list(final_item[df_cl_ItemName]))    
    final_item=final_item[final_item[language_dict.value.get('dfname_Unlockitem')].isin(unlock_selected)|(final_item[language_dict.value.get('dfname_Unlockitem')]=='')]
    final_item_count=final_item.groupby('稀有度')['稀有度'].count()
    final_item_count.columns=['数量']
    if debugmode:
        print(f'line{beginline+21}',final_item.shape[0],final_item_count,list(final_item[df_cl_ItemName]))
    intersection_list = list(set(ratiocal_columns) & set(dfroundinfo.columns.tolist()))
    ratioinfo=dfroundinfo[dfroundinfo['回合']==gameround][intersection_list]#.copy()
    #根据回合数生成字典和对应的权重，并过滤掉没有概率的东西
    rarity_map = dict(zip(ratioinfo.columns, ratioinfo.iloc[0]))
    count_map = dict(zip(final_item_count.index, final_item_count))
    if debugmode:
        print(f'line{beginline+28}',final_item.shape[0],rarity_map,count_map)
    final_item['weight'] = final_item['稀有度'].map(rarity_map).fillna(0)
    final_item['count'] = final_item['稀有度'].map(count_map).fillna(0)
    final_item=final_item[final_item['weight']>0]
    final_item.loc[final_item[translation_dict.get_text('dfname_Unlockitem')]=='宝石盒','weight']/=5
    totalweight=final_item['weight'].sum()
    final_item[df_cl_Chance]=final_item['weight']/final_item['count']*(5-min(5,max(0,locked_num)))
    bfiltered=False
    if ignorefilter!='':
        filterinfo=ignorefilter.split('.')
        if (len(filterinfo)==1):
            filterinfo.insert(0,language_dict.value.get(rt_filter_type,rt_filter_type))
        if (len(filterinfo)>1)&~(filterinfo[0] in final_item.columns):
            filterinfo.pop(0)
            filterinfo.insert(0,language_dict.value.get(rt_filter_type,rt_filter_type))
        list_of_filter=filterinfo[1].split(',')
        # 初始化一个空的布尔数组，用于存储最终的匹配结果
        combined_match = np.zeros(final_item.shape[0], dtype=bool)
        # 循环遍历每个过滤项，并更新 combined_match 数组
        for filter_item in list_of_filter:
            combined_match |= final_item[filterinfo[0]].isin(ApplyFilter_Regex(filter_item,final_item,filterinfo[0],dict_pinyin.get(filterinfo[0],'pinyin')))
        final_item = final_item[combined_match]        
        bfiltered=True
    if debugmode:
        print(f'line{beginline+52}',final_item.shape[0],totalweight,final_item[df_cl_Chance].sum(),ignorefilter,)
    final_item['original_index'] = final_item.index
    final_item.sort_values([df_cl_Chance,'original_index'],ascending=[False,True],inplace=True)
    final_item = final_item.drop('original_index', axis=1)
    if debugmode:
        print(f'line{beginline+57}',final_item.shape[0],final_item[[df_cl_ItemName,'weight',df_cl_Chance]])
    if rarity_selected!=language_dict.value.get('dfname_RarityList')[0]:
        final_item=final_item[final_item[df_cl_Rarity]==rarity_selected]
        bfiltered=True
    result=''
    
    if autoupdate:
        final_extra_text=''
        totalweight=round(final_item[df_cl_Chance].sum(),1)
        final_item[df_cl_Chance]=final_item[df_cl_Chance].round(1)
        result_df=final_item[[df_cl_ItemName,df_cl_Rarity,df_cl_Chance,'物品id']].copy()
        if bfiltered:
            label=language_dict.value.get('UI_shop_setting_format_filter','筛选后总概率')
            final_extra_text=f', {label}:{totalweight}%'
            if totalweight==0:                
                final_extra_text=language_dict.value.get('UI_Filter_zero_hint',', 请检查筛选或回合数，可能这回合没这个品质。')
            #额外计算期总期望和单品期望
            if (gameround<18)&~(result_df.empty):
                ratioinfo_next=dfroundinfo[dfroundinfo['回合']==(gameround+1)][intersection_list]
                if not(ratioinfo.iloc[0].equals(ratioinfo_next.iloc[0])):
                    nextdf=generate_actual_rate(
                        gameround=gameround + 1,
                        class_selected=class_selected,
                        ignorefilter=ignorefilter,
                        unlock_selected=unlock_selected,
                        other_class_activated=other_class_activated,
                        rarity_selected=rarity_selected,
                        locked_num=locked_num,
                        debugmode=False,
                        autoupdate=False,
                    )
                    totalweight_next=round(nextdf[df_cl_Chance].sum(),1)
                    result_df[df_cl_Chance+'_next']=nextdf[df_cl_Chance]#].copy()
                    diffprice=round(100/totalweight_next-100/totalweight,1)
                    if abs(diffprice)>0:
                        label=language_dict.value.get('UI_shop_next_round_diff','下回合搜到期望花费差值')
                        final_extra_text+=f', {label}:{diffprice}'
            result_df[language_dict.value.get('dfname_ExpectCount')]=round(100/result_df[df_cl_Chance],2)
            #开始处理格子的专属业务逻辑
            
            #有格子的情况下，才需要算参数
            bagcheck=final_item[final_item['标签'].str.contains('格子')].copy()
            if totalweight>0:
                expected_price_for_search=100/totalweight
                label=language_dict.value.get('UI_shop_ExpectSearchCost','另外搜到期望花费')
                final_extra_text+=f', {label}:{round(expected_price_for_search,1)}'
            final_bag_text=''
            if not(bagcheck.empty):                
                result_df[language_dict.value.get('dfname_Bagslots')]=final_item['核心参数值'].astype(int)
                result_df[language_dict.value.get('dfname_ROIname')]=round(final_item[language_dict.value.get('dfname_ROIname')].astype(float),2)
                average_param=round((bagcheck[df_cl_Chance]*bagcheck['核心参数值']).sum()/totalweight,2)
                average_price=round((bagcheck[df_cl_Chance]*bagcheck[language_dict.value.get('dfname_Costname')]).sum()/totalweight,1)
                average_roi=round(average_param/average_price,2)
                final_roi=round(average_param/(average_price+expected_price_for_search),2)

                label=language_dict.value.get('UI_shop_BagResult_Num','搜到包的格子数期望')                
                final_bag_text+=f'{label}:{average_param}'
                label=language_dict.value.get('UI_shop_BagResult_Cost','搜到后购买花费期望')          
                final_bag_text+=f', {label}:{average_price}'
                label=language_dict.value.get('UI_shop_BagResult_ROI','花费效率的期望')        
                final_bag_text+=f', {label}:{average_roi}'
                label=language_dict.value.get('UI_shop_BagResult_FinalROI','加上另外搜的成本后花费效率的期望')        
                final_bag_text+=f', {label}:{final_roi}'
            bag_extra_hint.value=final_bag_text
        extra_hint.value=final_extra_text
        #
        #在这个最后去匹配一下数据库，
        match_cl_name='物品id'
        value_column=[translation_dict.get_text('dfname_valuename'),match_cl_name]
        if debugmode:
            print(f'line{beginline+127}',dfItemValue.columns,value_column)
        value_clip=dfItemValue[dfItemValue['回合数']==gameround][value_column].copy()
        
        value_local_column=[df_cl_value,match_cl_name]
        if debugmode:
            print(f'line{beginline+132}',value_clip,value_local_column)
        value_clip.columns=value_local_column
        result_df=result_df.merge(value_clip,on=match_cl_name,how='left')#.fillna(0)
        result_df.sort_values(df_cl_value,ascending=False,inplace=True)
        result_df=result_df.fillna(language_dict.value.get('UI_itemvalue_None'))
        # result_df.loc[result_df[df_cl_value]==0,df_cl_value]=language_dict.value.get('UI_itemvalue_None')
        del result_df['物品id']
        shop_display_result.value=result_df
    else:
        final_item[df_cl_Chance]=final_item[df_cl_Chance].round(1)
        result=final_item[[df_cl_ItemName,df_cl_Rarity,df_cl_Chance,'核心参数值',language_dict.value.get('dfname_Costname')]].copy()
    if debugmode:
        print(f'line{beginline+144}',shop_display_result)
    return result


#公共设置开关
print_mode=False
language = reactive('zh')  # 默认语言设置为中文
version=' v0.9.7b0511    '

#维护一个翻译对应的字典，再从字典处理成更方便切换的最终字典。
translation_dict=Common.TranslationDict()#这个是我自己做的方法。。。差点忘记了，看来类封装真的很不错！

#考虑到可能的编码不兼容，文件名尽量不用中文，考虑到要兼容和快速另存更新
#一段内容一段内容处理完，不要穿插
#加载所有数据表，先不重新命名

FileNameKey='Data/Project_BPB_'
itemdata_path=FileNameKey+'Itemdata.xlsx'#0.9.7，来自飞书文档
dfitem=pd.read_excel(itemdata_path).fillna('')
dfitem.loc[dfitem['核心参数值']=='','核心参数值']=0

shopdata_path=FileNameKey+'Shopdata.xlsx'
dfroundinfo=pd.read_excel(shopdata_path).fillna('') #shop这个考虑重命名

battleinfo_path=FileNameKey+'Battledetail.xlsx'
dfroundbattleinfo=pd.read_excel(battleinfo_path).fillna('')


roundrecord_path=FileNameKey+'RoundRecord.xlsx'
dfroundbaseinfo=pd.read_excel(roundrecord_path).fillna('')

#以后有缘再做对局发育情况的记录

#一个一个处理多语言版本的信息，也先不重命名，如果有其他计算逻辑，这个可以后置一点
#注意管理冗余和引用

translation_dict.add_text('dfname_Classname', ['英雄', 'Class'])
translation_dict.add_text('dfname_Unlockitem', ['解锁道具', 'Unlockitem'])
translation_dict.add_text('dfname_Rarityname', ['稀有度', 'Rarity'])
translation_dict.add_text('dfname_Itemname', ['名称', 'Name'])
translation_dict.add_text('dfname_Chancename', ['概率', 'chance'])
translation_dict.add_text('dfname_Expectedname', ['期望产量', 'expect count'])
translation_dict.add_text('dfname_ROIname', ['花费效率', 'ROI'])
translation_dict.add_text('dfname_Costname', ['花费', 'Cost'])
translation_dict.add_text('dfname_valuename', ['记录中的参考回合战力', 'Reference RoundValue'])


dfitem[translation_dict.get_text('dfname_ROIname')]=dfitem['核心参数值']/dfitem['花费']
dfitem[translation_dict.get_text('dfname_ROIname','en')]=dfitem['核心参数值']/dfitem['花费']
dfitem[translation_dict.get_text('dfname_Costname','en')]=dfitem['花费']


translation_dict.add_text('badge_stone', ['石头', 'Stone'])
translation_dict.add_text('badge_rainbow', ['彩虹', 'Rainbow'])

ratiocal_columns=['普通', '罕见', '史诗','传说', '神级',  '特别']
raritieslist_zh=['all']+ratiocal_columns
translation_dict.generate_translation_list_from_df(dfitem,'dfname_Rarityname','dfname_RarityList',raritieslist_zh,base_key='zh')
translation_dict.generate_translation_list_from_df(dfitem,'dfname_Classname','dfname_HeroList')

result=[]
for language_use in ['zh', 'en']:
    herolist=translation_dict.get_text('dfname_HeroList',language_use).copy()
    if herolist[0] == '':
        herolist.pop(0)
    herolist.append(translation_dict.get_text('badge_stone', language_use))
    herolist.append(translation_dict.get_text('badge_rainbow', language_use))
    result.append(herolist)

translation_dict.add_text('dfname_SubClassList', result)

#UI的信息，以后再考虑改名
translation_dict.add_text('UI_appname', ['背包乱斗观测者', 'BPB_Analyzor'])
translation_dict.add_text('UI_class', ['选择职业', 'Select Class'])
translation_dict.add_text('UI_shop_unlock', ['选择解锁衍生物的道具', 'Select Gate Items'])
translation_dict.add_text('UI_shop_badge', ['设置徽章', 'Select Badge'])
translation_dict.add_text('UI_filter', ['过滤条件', 'filterinfo'])
translation_dict.add_text('UI_filter_tag_button', ['标签', 'tag'])
translation_dict.add_text('UI_gameround', ['回合数', 'round'])
translation_dict.add_text('UI_shop_lockedbag', ['锁定格子数', 'lockedItems'])
translation_dict.add_text('UI_shop_cal_ratio', ['计算', 'cal'])
translation_dict.add_text('UI_shop_cal_count', ['计算总产量', 'cal_count'])
translation_dict.add_text('UI_shop_setting_format', ['当前查看的回合数: {}, 每次刷新的商品数量: {}', 'Now Round: {}, goods num per refresh: {}'])
translation_dict.add_text('UI_shop_setting_format_class', ['选择职业', 'Class'])
translation_dict.add_text('UI_shop_setting_format_filter', ['筛选后总概率', 'Total chance after filter'])
translation_dict.add_text('UI_shop_next_round_diff', ['下回合搜到期望花费差值', 'expect diff'])
translation_dict.add_text('tag', ['标签', '标签'])#用来在业务里搜索，待改名成df前缀，最后再整理吧。
translation_dict.add_text('UI_shop_Result', ['#结果信息', '#ResultInfo'])
translation_dict.add_text('dfname_ExpectCount', ['期望搜索次数', 'ExpectSearchTimes'])
translation_dict.add_text('UI_shop_ExpectSearchCost', ['另外搜到期望花费', 'ExpectSearchCost'])
translation_dict.add_text('UI_shop_BagResult_Num', ['搜到包的格子数期望', 'ExpectBagSlots'])
translation_dict.add_text('UI_shop_BagResult_Cost', ['搜到后购买花费期望', 'ExpectBagCost'])
translation_dict.add_text('UI_shop_BagResult_ROI', ['花费效率的期望', 'ExpectBagROI'])
translation_dict.add_text('UI_shop_BagResult_FinalROI', ['加上另外搜的成本后花费效率的期望', 'ExpectfinalBagROI'])
translation_dict.add_text('dfname_Bagslots', ['格子数量', 'Bagslot'])
translation_dict.add_text('UI_ContactInfo', ['我正在结合AI进行ToB的企业开发创业~这真是一个好时代！', 'I am an entrepreneur currently leveraging AI to innovate in the B2B space. It is an exciting time to be shaping the future of business with technology.'])
translation_dict.add_text('UI_Filter_zero_hint', [', 请检查筛选或回合数，可能这回合没这个品质。', '. Please review the filters or the round settings; this quality may not appear in the shop for this round.'])
translation_dict.add_text('UI_itemvalue_None', ['无记录', 'NoData'])
translation_dict.add_text('UI_ContactTab', ['和我联系', 'Contact Me'])
translation_dict.add_text('UI_ShopTab', ['商店道具分析', 'Shop Analyze'])
translation_dict.add_text('UI_GalaryTab', ['画廊和数据下载', 'Galary & Data(ZH)'])
translation_dict.add_text('UI_RoundTab', ['记录回合情况', 'RoundInfo(ZH)'])
translation_dict.add_text('UI_BattleTab', ['记录战斗明细', 'BattleInfo(ZH)'])
translation_dict.add_text('UI_DonateInfo', ['这个人光顾着更新功能，连预留的捐赠码都忘记放上来了。 O.O ', 'This person was so engrossed in updating the features that he unexpectedly forgot to add the donation code.  (O.o)'])


#数据预处理

#一次性的加载出拼音搜索字段
dfitem = add_pinyin_column(dfitem, translation_dict.get_text('dfname_Itemname'))
dfitem = add_pinyin_column(dfitem, translation_dict.get_text('tag'),'tagpinyin')

dict_pinyin={
    translation_dict.get_text('dfname_Itemname'):'pinyin',
    translation_dict.get_text('tag'):'tagpinyin',
}

#处理解锁道具。其实标签最好也是中英的？
unlocklist_zh=sorted(dfitem[translation_dict.get_text('dfname_Unlockitem')].unique().tolist())#.sort()

dfunlockpack=dfitem[dfitem['名称'].isin(unlocklist_zh)][['名称','Name']].copy()
dfunlockpack.columns=['解锁道具',translation_dict.get_text('dfname_Unlockitem','en')]
#         print(dfunlockpack)
dfitem=dfitem.merge(dfunlockpack,on='解锁道具',how='left').infer_objects(copy=False).fillna('')
#处理完映射后建立清单
translation_dict.generate_translation_list_from_df(dfitem,'dfname_Unlockitem','dfname_UnlockList',bIgnoreBlank=True)

#开始处理第二部分功能模块的文本
translation_dict.add_text('additional_iteminfo', [['尖刺', '恢复','中毒', '吸血','生命上限', '疲惫','其他'], ['Spikes', 'Regeneration','Poison', 'Vampirism','maxHP', 'Fatigue','Other']])

additional_values = translation_dict.get_text('additional_iteminfo',language.value)
additional_values_pinyin=[get_pinyin_with_char(name) for name in additional_values]



#这里为了商店做一个拓展功能，上传的时候再计算一次，从记录根据清单找到id，然后提供当前回合的效果总和均值，精确到小数点两位



# 定义响应式变量
language_dict=reactive(translation_dict.get_language_dict(language.value))#文本字典库


# 定义完整的机制来源清单
defaultList=dfitem.sort_values('物品id')
itemlist_zh=language_dict.value.get('additional_iteminfo')+defaultList[translation_dict.get_text('dfname_Itemname')].unique().tolist()# 这里排序会有问题，导致新增的道具id变化，也就是说需要有一个真实的id和排序的显示，分开来。这些也先不管了，既然如此id应该在一个可靠的地方静态储存。
itemlist_id=list(range(1,len(additional_values)+1))+defaultList['物品id'].unique().tolist()
item_dict=dict(zip(itemlist_zh,itemlist_id))
# item_dict = {item: index + 1 for index, item in enumerate(itemlist_zh)}


def cal_item_value(df):
    #就用id，转换成对应语言，能做也要做，不能也要做。
    df_cl_ItemName=translation_dict.get_text('dfname_Itemname')
    df_value=df[df['效果类型id']!=4][['对局id','回合数','物品id','同名物品序号','每秒效果值']].copy()
    df_grouped = df_value.groupby(['对局id', '回合数', '物品id', '同名物品序号'])['每秒效果值'].sum().reset_index(name='总效果')
    # 注意：这里假设 '同名物品序号' 是从1开始的整数
    df_grouped['权重'] = 1 / df_grouped['同名物品序号'].astype(float)
    
    avg_effects = (df_grouped
                    .groupby(['物品id', '回合数'], as_index=False)
                    .apply(lambda group: round((group['总效果'] * group['权重']).sum() / group['权重'].sum(),2), include_groups=False)
                  )
    avg_effects.rename(columns={None:translation_dict.get_text('dfname_valuename')},inplace=True)
    avg_effects=avg_effects.merge(dfitem[['物品id',df_cl_ItemName,translation_dict.get_text('dfname_Itemname','en')]],on='物品id',how='left')

    return avg_effects
#但数据不实时更新，加载的时候才计算一次，要用的地方和函数写一起挺好
dfItemValue=cal_item_value(dfroundbattleinfo)

#定义当前界面的响应变量，可以考虑改名了

hero = reactive(language_dict.value.get('dfname_HeroList')[0])
unlock_items = reactive([])
round_num = reactive((1,18))
ignore_filter = reactive("")
rarity = reactive(language_dict.value.get('dfname_RarityList')[0])
shop_display_result=reactive(pd.DataFrame())
hero_badge = reactive([])
locked_pos_num = reactive(0)
extra_hint = reactive('')
bag_extra_hint = reactive('')
default_filter_column = reactive(language_dict.value.get('dfname_Classname'))
language_Lable = reactive('中文')  # 默认语言设置为中文
initialing = reactive(True)
    
@solara.component
def Contact_Me():
    with solara.Card("Contact me", margin=0, elevation=0):
        with solara.Column():
            # label=language_dict.value.get('UI_ContactInfo')
            solara.Text(language_dict.value.get('UI_ContactInfo'))
            solara.Markdown("""                
            Email: asdanika@gmail.com

            discord: izumi.qu#5605
            
            Wechat: aiding0905""")
            solara.Image('Image/art_code.png',width='170px')
            # label=language_dict.value.get('UI_DonateInfo')
            solara.Text(language_dict.value.get('UI_DonateInfo'))
                # solara.Image('art_Reaper.png',width='170px')
                # solara.Image('art_Pyromancer.png',width='170px')
                # solara.Image('art_Berserker.png',width='170px')
                # solara.Image('art_Ranger.png',width='170px')       

@solara.component
def BPB_Analyze():
    df_cl_Expect=language_dict.value.get('dfname_Expectedname')
    df_cl_Chance=language_dict.value.get('dfname_Chancename')
    df_cl_ItemName=language_dict.value.get('dfname_Itemname')
    df_cl_Rarity=language_dict.value.get('dfname_Rarityname')
    def modirate_round(**kwargs):
        generate_actual_rate(round_num.value[0],hero.value,ignore_filter.value,unlock_items.value,hero_badge.value,rarity.value,locked_pos_num.value,debugmode=False)
        return

    def total_count(**kwargs):
        #在计算之前重复的部分用临时变量调用
        
        resultdf=pd.DataFrame()
        for roundinfo in range(round_num.value[0],round_num.value[1]+1):
            newresult=generate_actual_rate(roundinfo,hero.value,ignore_filter.value,unlock_items.value,hero_badge.value,rarity.value,locked_pos_num.value,debugmode=False,autoupdate=False)
            newresult['回合']=roundinfo
            if resultdf.empty:
                resultdf=newresult
            else:
                resultdf=pd.concat([resultdf,newresult])
        resultdf[df_cl_Expect]=resultdf[df_cl_Chance]/100
        resultdf.loc[resultdf['回合']<4,df_cl_Expect]*=3
        resultdf.loc[resultdf['回合']>=4,df_cl_Expect]*=4
        shop_display_result.value=resultdf.groupby([df_cl_ItemName,df_cl_Rarity,language_dict.value.get('dfname_Costname')],as_index=False)[[df_cl_Expect]].sum().round(2)
        return
    def modirate_round_takeargs(args):
        generate_actual_rate(round_num.value[0],hero.value,ignore_filter.value,unlock_items.value,hero_badge.value,rarity.value,locked_pos_num.value,debugmode=False)
        return
    # with solara.Sidebar():
    #     Contact_Me()
    with solara.AppBarTitle():
        solara.Text(language_dict.value.get('UI_appname','背包乱斗观测者')+version)
        solara.ToggleButtonsSingle(
            value=language_Lable,
            values=['中文', 'English'],
            on_value=change_language
        )
    with solara.Row():
        with solara.Card(language_dict.value.get('UI_class','选择职业')):
            solara.ToggleButtonsSingle(value=hero, values=language_dict.value.get('dfname_HeroList'),on_value=modirate_round_takeargs)
        with solara.Card(language_dict.value.get('UI_shop_unlock','解锁衍生物的道具')):
            solara.ToggleButtonsMultiple(value=unlock_items, values=language_dict.value.get('dfname_UnlockList'),on_value=modirate_round_takeargs)
    with solara.Row():
        solara.SelectMultiple(label=language_dict.value.get('UI_shop_badge','设置徽章职业'), values=hero_badge, all_values=language_dict.value.get('dfname_SubClassList'),on_value=modirate_round_takeargs)
        solara.Select(label=df_cl_Rarity, value=rarity, values=language_dict.value.get('dfname_RarityList'),on_value=modirate_round_takeargs)
        solara.InputText(label=language_dict.value.get('UI_filter','过滤条件'),value=ignore_filter,on_value=modirate_round_takeargs,continuous_update=True),
        solara.ToggleButtonsSingle(value=default_filter_column, values=[df_cl_ItemName,language_dict.value.get('UI_filter_tag_button','标签')],on_value=modirate_round_takeargs)
    with solara.Row():
        solara.SliderRangeInt(language_dict.value.get('UI_gameround','回合数:'),value=round_num,min=1,max=18,on_value=modirate_round_takeargs)
        solara.SliderInt(language_dict.value.get('UI_shop_lockedbag','锁定格子数:'),value=locked_pos_num,min=0,max=5,on_value=modirate_round_takeargs)
        solara.Button(language_dict.value.get('UI_shop_cal_ratio',"计算"), on_click=modirate_round)
        solara.Button(language_dict.value.get('UI_shop_cal_count',"计算总产量"), on_click=total_count)
    select_output=language_dict.value.get('UI_shop_setting_format','当前查看的回合数: {}, 每次刷新的格子: {}').format(round_num.value[0],5-min(5,max(0,locked_pos_num.value)))
    if hero.value:
        label=language_dict.value.get('UI_shop_setting_format_class',"选择职业")
        select_output+=f', {label}: {hero.value}'
    select_output+=extra_hint.value
    if initialing.value:
        modirate_round()
        initialing.value=False
    solara.Markdown(language_dict.value.get('UI_shop_Result',"#结果展示"))
    with solara.Columns([1,1.5]):
        solara.DataFrame(shop_display_result.value, items_per_page=5)
#         with solara.Card(title='结果信息'):
        with solara.Column():
            solara.Markdown(select_output)#,[1,18]) 
            solara.Markdown(bag_extra_hint.value)#,[1,18]) 
        # rv.Img(src='Reaper.png', contain=True, max_height="200px")
#     with solara.Card():
#         solara.Markdown("### 如果您觉得我的项目对您有帮助,欢迎捐赠以资赞助 :)"),
# #         with solara.Hbox():
#         solara.Link("PayPal 捐赠", href="https://www.paypal.me/YOUR_PAYPAL"),
#         solara.Link("支付宝捐赠", href="https://qr.alipay.com/YOUR_ALIPAY_QR"),
#         solara.Link("比特币捐赠", href="bitcoin:YOUR_BTC_ADDRESS"),
#         solara.Markdown("#### 所有捐赠将用于项目的持续开发和服务器运营,衷心感谢您的支持!")
#     solara.Info(select_output)#,[1,18]) 


# 可以做一个自动加载和重置，两套数据解决，增加一个重置按钮
latestround=dfroundbaseinfo.iloc[-1]
default_key=latestround.keys()
maxrecord=dfroundbaseinfo['对局id'].max()
default_value=[maxrecord,'高胜的一局',1,11,True,'',14,1,'',6,17]
defaultsetting=dict(zip(default_key,default_value))
# defaultsetting={
# "对局id":4
# "对局名称":"女巫彩虹局"
# "回合数":18
# "对局持续时长":25.0
# "胜败情况":True
# "经济":""
# "背包格":60
# "主职":4
# "转职":""
# "分段":"6
# "分段值":17
#和round格式一致，方便整体切换，那这个就是一个字典，这几个数据储存已经分了id，最后可能还要根据语言在导入导出的时候做一次切换


dfRBase_gameid=reactive(maxrecord)
dfRBase_gamename=reactive('女巫彩虹锅')
dfRBase_roundnum=reactive(1)
dfRBase_roundtime=reactive(10.7)
dfRBase_roundwin=reactive(True)
dfRBase_roundslots=reactive(17)
dfRBase_roundclassname=reactive('火焰魔导士')#这里存id再去找，实在不行可以用calvalue的方法再定义一个？当然或许也可以反过来，交互的是文本，存的是id
dfRBase_roundsubclassname=reactive('')#这里存id再去找，实在不行可以用calvalue的方法再定义一个？当然或许也可以反过来，交互的是文本，存的是id
dfRBase_roundrank=reactive('钻石')
dfRBase_roundranknum=reactive(38)
dfRBase_modifyslot=reactive(4)
UI_setting_text=reactive('')


#倒序处理对局记录，做个复制。
df=dfroundbaseinfo.iloc[::-1].fillna("").copy()
df['胜败情况'] = np.where(df['胜败情况'] == False, '失败', '胜利')
display_Gameinfo=reactive(df.copy())


df['对局清单']=df['对局id'].astype(str)+':'+df['对局名称']
roundlist=df['对局清单'].unique().tolist()

rank_list_zh=['娱乐','青铜','白银','黄金','白金','钻石','大师','特级大师','超级大爷']
rank_dict = {item: index + 1 for index, item in enumerate(rank_list_zh)}

# 定义额外的值

itemlist_zh=language_dict.value.get('additional_iteminfo')+sorted(dfitem[translation_dict.get_text('dfname_Itemname')].unique().tolist())# 这里排序会有问题，导致新增的道具id变化，也就是说需要有一个真实的id和排序的显示，分开来。这些也先不管了，既然如此id应该在一个可靠的地方静态储存。

item_dict = {item: index + 1 for index, item in enumerate(itemlist_zh)}
# itemlist_zh=sorted(dfitem[translation_dict.get_text('dfname_Itemname')].unique().tolist())
#dict可以再取一个不排序的就可以，但这意味着以后也不能排序，只能新增

dfBBattle_ItemName=reactive('木剑')#这里肯定是显示文本了，先做一个下拉再去问，存的话可以考虑存成id，这主要是为了最后的数据翻译和共享。
dfBBattle_ItemNameList=reactive(itemlist_zh)#这里肯定是显示文本了，先做一个下拉再去问，存的话可以考虑存成id，这主要是为了最后的数据翻译和共享。
dfBBattle_Itemid=reactive(1)#默认1，重复记录再加？
dfBBattle_ItemisMine=reactive(True)
dfBBattle_ItemType=reactive('伤害')#也是一样，显示文本，存数字，伤害，治疗，护甲，魔法值
dfBBattle_ItemEffect=reactive(11)
dfBBattle_extrahint=reactive('')
display_round=reactive(pd.DataFrame())
display_lastround=reactive(pd.DataFrame())
dfBBattle_extratrigger=reactive('')
triggerlist=['']+additional_values[:-1]
dfBBattle_displaycat=reactive(False)

dfBBattle_extraroundlist=reactive(roundlist)
if len(roundlist):
    defaultname=roundlist[0]
else:
    defaultname='高胜的一局'
dfBBattle_extraroundname=reactive([defaultname])

trigger_dict = {item: index + 1 for index, item in enumerate(triggerlist)}

dfBBattle_EditorRow=reactive(-1)
dfBBattle_EditorMode=reactive(True)
dfBBattle_EditorPreRound=reactive(0)

itemeffect_list_zh=['伤害','治疗','护盾','魔法']
itemeffect_dict = {item: index + 1 for index, item in enumerate(itemeffect_list_zh)}
dfBBattle_displaycatdetail=reactive(itemeffect_list_zh[:-1])

classlist=language_dict.value.get('dfname_HeroList').copy()
classlist.pop(0)
class_dict = {item: index + 1 for index, item in enumerate(classlist)}

BR_translation_dict=Common.TranslationDict()
BR_translation_dict.add_text('appname', ['背包乱斗记录者', 'BPB_Recorder'])
# language = reactive('zh')  # 默认语言设置为中文

# version=' v0.9.7    '


Record_initialing = reactive(True)
# 定义响应式变量
BR_language_dict=reactive(BR_translation_dict.get_language_dict(language.value))#文本字典库

echart_total=reactive({'title': {'text': '对局战力趋势'},
 'tooltip': {},
 'legend': {'data': ['狂战局-我方']},
 'xAxis': {'data': [1, 2]},
 'yAxis': {},
 'series': [{'name': '狂战局-我方', 'type': 'line', 'data': [5.79, 1.68]}]}
                     )
echart_detail=reactive({'title': {'text': '对局数据明细'},
 'tooltip': {},
 'legend': {'data': ['木剑', '铲铲']},
 'xAxis': {'data': [1, 2]},
 'yAxis': {},
 'series': [{'name': '木剑', 'type': 'line', 'data': [1.03, 1.21]},
  {'name': '铲铲', 'type': 'line', 'data': [1.53, 2.21]}]}
                      )


def set_roundinfo(dict):#初始化加载要等reaction和字典都建立好了才可以用
    #加载已有数据，方便后续时间
    dfRBase_gameid.value=dict['对局id']
    dfRBase_gamename.value=dict['对局名称']
    dfRBase_roundnum.value=dict['回合数']
    dfRBase_roundslots.value=dict['背包格']
    # jobid=dict['主职']
    dfRBase_roundclassname.value=classlist[dict['主职']-1]
    dfRBase_roundrank.value=rank_list_zh[dict['分段']-1]
    dfRBase_roundranknum.value=dict['分段值']
    #核心就是要做另外一种初始化。那既然是初始化，就在初始化那边调用就好了。
    
    return

def cal_line_graphic(df,title='每秒效果值',cal_total=False):
    #绘图还要加上基础功能，选项折叠，快速勾选，只看某个和重置e'ch
    if cal_total:
        if dfBBattle_displaycat.value:
            line_columns=['对局名称', '战斗角色','效果类型', '回合数']
            df=df[df['效果类型'].isin(dfBBattle_displaycatdetail.value)]
        else:
            df=df[df['效果类型id']!=4]
            line_columns=['对局名称', '战斗角色', '回合数']        
        grouped = df.groupby(line_columns)['每秒效果值'].sum().round(2).reset_index()
        #加入是否分类显示
    else:
        line_columns=['物品名', '同名物品序号', '回合数']
        df['同名物品序号']=df['同名物品序号'].astype(str)
        grouped = df.groupby(line_columns)['每秒效果值'].mean().round(2).reset_index()
    # 获取x轴的唯一回合数列表
    x_axis = sorted(grouped[line_columns[-1]].unique())
    # 构建每个组合的数据列表
    series_data = []
    for name, group in grouped.groupby(line_columns[0:-1]):
        item_data = [group[group[line_columns[-1]] == r]['每秒效果值'].iloc[0] if r in group[line_columns[-1]].values else None for r in x_axis]
        new_series_data={
            'name': f"{name[0]}({'.'.join(name[1:])})",
            'type': 'line', 
            'data': item_data
        }
        if (cal_total)and(name[1]=='自己'):
            new_series_data['label']={
                'show': True,
                'position': 'bottom',
            }
        series_data.append(new_series_data)

    toolbox_config = {
        "feature": {
            "saveAsImage": {},
            "magicType": {"type": ["line", "bar"]},
            "restore": {},
            "dataView": {},
            "dataZoom": {
                "show": True,
                "title": {"zoom": "区域缩放", "back": "区域缩放还原"}
            }
        }
    }
    final_option={
        "title": {"text": title},
        "tooltip": {},
        "legend": {"data": [d['name'] for d in series_data]},
        "xAxis": {"data": x_axis},
        "yAxis": {},
        "series": series_data,
        "toolbox": toolbox_config
    }
    if len(series_data)>2:
        final_option['legend']['type']='scroll'
        final_option['legend']['orient']='vertical'
        final_option['legend']['right']=0
        final_option['legend']['top']=20
        final_option['legend']['bottom']=20
        final_option['grid']={
            'right':'20%'
        }
    return final_option

@solara.component
def BPB_Record():
    cell, set_cell = solara.use_state(cast(Dict[str, Any], {}))

    #筛选和快速填写功能
    def ApplyFilter(args):
        namelabel=language_dict.value.get('dfname_Itemname')
        # namelabel=translation_dict.get_text('dfname_Itemname',language.value)
        itemlist_new=ApplyFilter_Regex(args,dfitem,namelabel)
        if len(itemlist_new)==0:
            dfBBattle_extrahint.value=', 没搜到匹配道具，列表未更新'
        else:
            dfBBattle_extrahint.value=f', 搜索到{len(itemlist_new)}个道具'
            dfBBattle_ItemNameList.value=itemlist_new
            dfBBattle_ItemName.value=itemlist_new[0]
            dfBBattle_Itemid.value=1
        return

        
    #快速填写是一个新增模式，先跑通这个，后续再考虑增加一键复制，以及以后导入官方的日志
    def on_action_cell_fastenter(column, row_index, data_source):
        selected_value = data_source.iloc[row_index]
        real_row=selected_value['index']
        real_value=dfroundbattleinfo.iloc[real_row]
        item_select_filter.value=''
        dfBBattle_ItemEffect.value=real_value['效果数值']
        dfBBattle_ItemName.value=real_value['物品名']
        dfBBattle_ItemType.value=real_value['效果类型']
        
        dfBBattle_ItemisMine.value=(real_value['战斗角色']=='自己')
        dfBBattle_Itemid.value=real_value['同名物品序号']
        dfBBattle_extratrigger.value=real_value['间接作用机制']
        exitEdit()
        
    def on_action_cell_editrecord(column, row_index, data_source):
        selected_value = data_source.iloc[row_index]
        real_row=selected_value['index']
        on_action_cell_fastenter(column, row_index, data_source)
        real_value=dfroundbattleinfo.iloc[real_row]
        #除了这些，还有其他的值
        dfRBase_roundtime.value=real_value['对局持续时长']
        dfBBattle_EditorPreRound.value=dfRBase_roundnum.value
        dfRBase_roundnum.value=real_value['回合数']
        
        dfBBattle_EditorRow.value=real_row
        dfBBattle_EditorMode.value=False              

    def render_dataframe(df, column_filter=None,check_column='对局id'):
        columns = df
        if check_column in df.columns:
            if column_filter:
                columns = columns[column_filter]
        # style = {
        #     'transform': 'translateX(-20px)',  # 向左偏移 20 像素
        #     'position': 'relative'  # 确保 transform 属性生效
        # }                
        return solara.DataFrame(
            columns,
            items_per_page=10,
            cell_actions=[
                solara.CellAction(
                    icon="mdi-content-duplicate",
                    name="快速填写",
                    on_click=lambda row, col: on_action_cell_fastenter(row, col, df),
                ),
                solara.CellAction(
                    icon="mdi-pencil",
                    name="编辑记录",
                    on_click=lambda row, col: on_action_cell_editrecord(row, col, df),
                )
            ]
        )        
    def RevertBattleInfo(**kwargs):
        global dfroundbattleinfo
        dfroundbattleinfo=dfroundbattleinfo[:-1]
        dfRBI=RecalUIDataFrame(dfroundbattleinfo,False)
        UpdateGraphic(dfRBI.copy())
        UpdateUIDataFrame(dfRBI.copy())
    def UpdateUIDataFrame(dfRBI):
        # global testdf
        # testdf=dfRBI.copy()
        # print(len(dfRBI),dfRBI)
        
        dfRBI=dfRBI[dfRBI['对局id']==dfRBase_gameid.value]#[['回合数','物品名','每秒效果值','效果类型','战斗角色','同名物品序号']]
        # print(len(dfRBI),dfRBI)
        display_round.value=dfRBI[dfRBI['回合数']==dfRBase_roundnum.value].reset_index(drop=True)#切片赋值给预览那边，上回合的也预览
        if dfRBase_roundnum.value>1:
            display_lastround.value=dfRBI[dfRBI['回合数']==(dfRBase_roundnum.value-1)].reset_index(drop=True)#切片赋值给预览那边，上回合的也预览
        else:
            display_lastround.value=pd.DataFrame()
    def UpdateReference(args):
        dfRBI=RecalUIDataFrame(dfroundbattleinfo,False)
        UpdateGraphic(dfRBI.copy())
        
    def UpdateGraphic(dfRBI):
        gamelist=dfBBattle_extraroundname.value
        gameidlist=[int(game.split(":")[0]) for game in gamelist]
        if len(gameidlist)<=1:
            dfRBI=dfRBI[dfRBI['对局id'].isin(gameidlist+[dfRBase_gameid.value])]#[['回合数','物品名','每秒效果值','效果类型','战斗角色','同名物品序号']]
        else:
            top_gameids = sorted(gameidlist, reverse=True)[:3]
            dfRBI = dfRBI[((dfRBI['对局id'].isin(top_gameids)) & (dfRBI['战斗角色'] == '自己'))|(dfRBI['对局id'] == dfRBase_gameid.value)]
        dfRBI['物品名'] = dfRBI['物品名'].str.replace('(New)', '', regex=False)
        # print(gameidlist)
        # dfRBI=dfRBI[dfRBI['对局id']==dfRBase_gameid.value]#[['回合数','物品名','每秒效果值','效果类型','战斗角色','同名物品序号']]
        
        echart_total.value=cal_line_graphic(dfRBI,'对局战力趋势',cal_total=True)
        dfRBI=dfRBI[dfRBI['对局id']==dfRBase_gameid.value]#[['回合数','物品名','每秒效果值','效果类型','战斗角色','同名物品序号']]
        # dfRBI=dfRBI[dfRBI['对局名称']==dfRBase_gamename.value]#[['回合数','物品名','每秒效果值','效果类型','战斗角色','同名物品序号']]
        echart_detail.value=cal_line_graphic(dfRBI[dfRBI['对局id']==dfRBase_gameid.value],'对局数据明细')
        
    def RecalUIDataFrame(df,bNewline=True):        
        df['每秒效果值']=round(df['效果数值']/df['对局持续时长'],2)
        df['战斗角色'] = np.where(df['是否属于我方'] == False, '对手', '自己')        
        dflist=[]
        if bNewline:
            dflist.append(df.iloc[[-1]].copy())
            dflist.append(df[:-1].copy())
            dflist[0]['物品名']+='(New)'
        else:
            dflist.append(df.copy())

        dflist[-1].sort_values(['是否属于我方','效果类型id','每秒效果值'],ascending=[False,True,False],inplace=True)
        dfRBI = pd.concat(dflist)#保持原来的index，方便引用修改
        dfRBI=dfRBI.reset_index()
        return dfRBI
        
    def AddBattleInfo(**kwargs):
        #制作新数据
        #修改公共数据值
        #制作并更新预览数据（可以传入新数据，再另外做切片
        #更新绘图数据
        global dfroundbattleinfo
        finalhint='。记录已新增，展示在表格的第一行（带new）'
        new_row = {
            '对局id': dfRBase_gameid.value,
            '对局名称': dfRBase_gamename.value,
            '回合数': dfRBase_roundnum.value,
            '对局持续时长': dfRBase_roundtime.value,

            '物品id': item_dict.get(dfBBattle_ItemName.value,0),
            '物品名': dfBBattle_ItemName.value,
            '是否属于我方': dfBBattle_ItemisMine.value,
            
            '同名物品序号': dfBBattle_Itemid.value,
            '效果类型id': itemeffect_dict.get(dfBBattle_ItemType.value,0),
            '效果类型': dfBBattle_ItemType.value,
            '效果数值': dfBBattle_ItemEffect.value,
            '间接作用机制': dfBBattle_extratrigger.value,
            '间接作用机制id': trigger_dict.get(dfBBattle_extratrigger.value,0),
        }
        
        if dfBBattle_EditorRow.value>=0:#这是编辑模式
            if dfBBattle_EditorRow.value in dfroundbattleinfo.index:
                for key, value in new_row.items():
                    dfroundbattleinfo.at[dfBBattle_EditorRow.value, key] = value
                finalhint='。编辑的行已经更新，退出编辑模式，可以继续填写啦！'
                # value_previous = solara.use_previous(dfRBase_roundnum.value)
                # dfRBase_roundnum.value=value_previous
                
            else:
                finalhint='。要编辑的行在记录中没找到，已退出编辑模式，重新保存即可新增。'
                

            
        elif dfroundbattleinfo.empty:
            dfroundbattleinfo = pd.DataFrame([new_row],columns=dfroundbattleinfo.columns)
        else:
            dfroundbattleinfo = pd.concat([dfroundbattleinfo, pd.DataFrame([new_row])], ignore_index=True)
        exitEdit()
        dfRBI=RecalUIDataFrame(dfroundbattleinfo,dfBBattle_EditorRow.value<0)
        # print(dfRBI)
        UpdateGraphic(dfRBI.copy())
        UpdateUIDataFrame(dfRBI.copy())
        # if dfBBattle_EditorRow.value
        # dfBBattle_EditorRow.value=-1
        # dfBBattle_EditorMode.value=True        
        dfBBattle_extrahint.value=finalhint
        dfBBattle_extratrigger.value=''
        return
    def NewRoundInfo(**kwargs):

        latestround=dfroundbaseinfo.iloc[-1]
        default_key=latestround.keys()        
        maxrecord=dfroundbaseinfo['对局id'].max()+1
        default_value=[maxrecord,'高胜的一局',1,11,True,'',14,1,'',6,17]
        defaultsetting=dict(zip(default_key,default_value))
        set_roundinfo(defaultsetting)            
        
    def AddRoundInfo(**kwargs):
        global dfroundbaseinfo
        new_row = {
            '对局id': dfRBase_gameid.value,
            '对局名称': dfRBase_gamename.value,
            '回合数': dfRBase_roundnum.value,
            '对局持续时长': dfRBase_roundtime.value,
            
            '胜败情况': dfRBase_roundwin.value,
            '背包格': dfRBase_roundslots.value,
            '主职': class_dict.get(dfRBase_roundclassname.value,0),
            # 'roundsubclassname': roundsubclassname,
            '分段': rank_dict.get(dfRBase_roundrank.value,0),
            '分段值': dfRBase_roundranknum.value
        }
        if dfroundbaseinfo.empty:
            dfroundbaseinfo = pd.DataFrame([new_row],columns=dfroundbaseinfo.columns)            
        else:            
            dfroundbaseinfo = pd.concat([dfroundbaseinfo, pd.DataFrame([new_row])], ignore_index=True)
        df=dfroundbaseinfo.iloc[::-1].fillna("").copy()
        df['胜败情况'] = np.where(df['胜败情况'] == False, '失败', '胜利')
        display_Gameinfo.value=df

        df['对局清单']=df['对局id'].astype(str)+':'+df['对局名称']
        # roundlist=df['对局清单'].unique().tolist()
        # df['对局清单']=df['对局id']+':'+df['对局名称']
        roundlist=df['对局清单'].unique().tolist()
        if roundlist!=dfBBattle_extraroundlist.value:
            dfBBattle_extraroundlist.value=roundlist.copy()
        return
    def additemid(**kwargs):
        dfBBattle_Itemid.value+=1
    def minusitemid(**kwargs):
        if dfBBattle_Itemid.value>1:
            dfBBattle_Itemid.value-=1
    def exitEdit(**kwargs):
        dfBBattle_EditorRow.value=-1
        dfBBattle_EditorMode.value=True
        dfBBattle_extrahint.value=''
        # value_previous = solara.use_previous(dfRBase_roundnum.value)
        if dfBBattle_EditorPreRound.value>0:
            dfRBase_roundnum.value=dfBBattle_EditorPreRound.value
            dfBBattle_EditorPreRound.value=0

    def handle_file(file_info,target_df):
        global dfroundbattleinfo
        global dfroundbaseinfo
        global dfItemValue
        # global filedetail
        # filedetail=file_info
        
        redraw=target_df.equals(dfroundbattleinfo)
        reloadbase=target_df.equals(dfroundbaseinfo)
        if file_info['name'].endswith('.csv'):
            file_text = file_info['data'].decode('utf-8')
            target_df = pd.read_csv(io.StringIO(file_text))
        elif file_info['name'].endswith('.xlsx'):
            target_df = pd.read_excel(file_info['file_obj'])
        else:
            print("Unsupported file format.")                
            return
        UI_setting_text.value=f'{file_info["name"]}文件已加载好'
        if redraw:
            dfRBI=RecalUIDataFrame(target_df,False)
            # print(dfRBI)
            UpdateGraphic(dfRBI.copy())
            UpdateUIDataFrame(dfRBI.copy())            
            dfItemValue=cal_item_value(target_df)
        if reloadbase:
            df=target_df.iloc[::-1].fillna("").copy()
            df['胜败情况'] = np.where(df['胜败情况'] == False, '失败', '胜利')
            display_Gameinfo.value=df
    
            df['对局清单']=df['对局id'].astype(str)+':'+df['对局名称']
            # roundlist=df['对局清单'].unique().tolist()
            # df['对局清单']=df['对局id']+':'+df['对局名称']
            roundlist=df['对局清单'].unique().tolist()
            if roundlist!=dfBBattle_extraroundlist.value:
                dfBBattle_extraroundlist.value=roundlist.copy()        
        
    # with solara.AppBarTitle():
    #     solara.Text(BR_language_dict.value.get('appname','背包乱斗记录者')+version)
        
    with solara.lab.Tabs(vertical=True):
        with solara.lab.Tab(language_dict.value.get('UI_BattleTab','记录战斗明细')):
            with solara.Columns([1,1,1,1]):
                with solara.Column():
                    #回合数靠功能增减，但对于核心数据，最好进单表，不用，merge其实很快。
                    #录入的部分，和结果预览的部分（本回合已有数据），以及整个对局的预览
                    item_select_filter = solara.use_reactive("")  # another possibility
                    with solara.Columns([2,2,2,2,1,1]):
                        solara.InputText(BR_language_dict.value.get('gameround','搜索道具'),value=item_select_filter,on_value=ApplyFilter,continuous_update=True)#,[1,18])
                        solara.Select(label=BR_language_dict.value.get('dfname_Itemname','道具名'), value=dfBBattle_ItemName, values=dfBBattle_ItemNameList.value)
                        solara.InputInt(BR_language_dict.value.get('itemid','同名物品序号'), value=dfBBattle_Itemid, continuous_update=True)
                        solara.Select(label=BR_language_dict.value.get('dfname_extratriggername','间接作用机制'), value=dfBBattle_extratrigger, values=triggerlist)
                        solara.Button('-', on_click=minusitemid, small=True)
                        solara.Button('+', on_click=additemid, small=True)
        
                    solara.InputInt(BR_language_dict.value.get('itemeffect','物品效果值'), value=dfBBattle_ItemEffect, continuous_update=True)
                    solara.SliderInt("", value=dfBBattle_ItemEffect, min=-500, max=10000)
                    solara.ToggleButtonsSingle(value=dfBBattle_ItemType, values=BR_language_dict.value.get('effect_list',itemeffect_list_zh))#,label=classname)
                    solara.Checkbox(label=BR_language_dict.value.get('ItemisMine','是否我的道具'), value=dfBBattle_ItemisMine)
                    # solara.SliderRangeInt(BR_language_dict.value.get('gameround','回合数:'),value=round_num,min=1,max=18,on_value=modirate_round_takeargs)#,[1,18])
                    solara.InputFloat(BR_language_dict.value.get('roundtime','战斗时间'), value=dfRBase_roundtime, continuous_update=True)
                    solara.SliderFloat("", value=dfRBase_roundtime, min=0, max=60)
                    solara.InputInt(BR_language_dict.value.get('roundnum','回合数'), value=dfRBase_roundnum, continuous_update=True)
                    solara.SliderInt('', value=dfRBase_roundnum, min=1, max=18)
                    #filter
                    #select
                    #solara.SliderInt("", value=dfBBattle_Itemid, min=1, max=10)
                    label=f"当前对局id: {dfRBase_gameid.value}，当前对局: {dfRBase_gamename.value}{dfBBattle_extrahint.value}"
                    if dfBBattle_EditorRow.value>=0:
                        dfBBattle_extrahint.value=', 正在编辑已有记录'
                    solara.Markdown(label)
                    with solara.Row():
                        solara.Button(BR_language_dict.value.get('save_battleinfo',"保存"), on_click=AddBattleInfo)
                        solara.Button(BR_language_dict.value.get('save_revertbattleinfo',"删除最近新增记录"), on_click=RevertBattleInfo)
                        solara.Button(BR_language_dict.value.get('save_updategraphic',"退出编辑"),disabled=dfBBattle_EditorMode.value, on_click=exitEdit)
                with solara.Column():
                        
                    solara.Markdown(BR_language_dict.value.get('UI_lastroundinfo','###上回合记录'))
                    
                    render_dataframe(
                        display_lastround.value,
                        column_filter=['物品名', '每秒效果值','效果数值', '效果类型','间接作用机制', '战斗角色', '同名物品序号']
                    )
                    solara.Markdown(BR_language_dict.value.get('UI_roundinfo','###当前回合已有记录'))
                    
                    render_dataframe(
                        display_round.value,
                        column_filter=['物品名', '每秒效果值','效果数值', '效果类型','间接作用机制', '战斗角色', '同名物品序号']
                    )
                with solara.Column():
                    with solara.Row():
                        solara.Checkbox(label=BR_language_dict.value.get('ItemisMine','是否分类显示'), value=dfBBattle_displaycat,on_value=UpdateReference)
                        solara.SelectMultiple(label=BR_language_dict.value.get('dfname_Itemname','额外参考对局'), values=dfBBattle_extraroundname, all_values=dfBBattle_extraroundlist.value,on_value=UpdateReference)#,multiple=True)
                        solara.SelectMultiple(label=BR_language_dict.value.get('dfname_Itemname','分类显示值'), values=dfBBattle_displaycatdetail, all_values=itemeffect_list_zh,on_value=UpdateReference)#,multiple=True)
                        # solara.Select(label=BR_language_dict.value.get('dfname_Itemname','额外参考对局'), value=dfBBattle_extraroundname, values=dfBBattle_extraroundlist.value)#这里做多选，lazy加载
                        
                    #加一个显示切换，全部还是分大类，以及一个额外参考对局战力
                    solara.FigureEcharts(option=echart_total.value)
                    solara.FigureEcharts(option=echart_detail.value)
                    # solara.FigureEcharts()
                    
                    #绘图，有折线图的话其实或许可以一张图？但过滤会麻烦所以还是两张图吧。
                    
            #还需要一个地方同时预览输入的效果，也就是plot曲线，也要支持修改历史记录
        with solara.lab.Tab(language_dict.value.get('UI_RoundTab','记录回合情况')):
            with solara.Columns([2,1]):
                with solara.Column():
                    solara.InputText(BR_language_dict.value.get('gamename','对局名称'),value=dfRBase_gamename)#,[1,18])
                    solara.InputInt(BR_language_dict.value.get('roundnum','回合数'), value=dfRBase_roundnum, continuous_update=True)
                    solara.SliderInt('', value=dfRBase_roundnum, min=1, max=18)
                    solara.InputFloat(BR_language_dict.value.get('roundtime','战斗时间'), value=dfRBase_roundtime, continuous_update=True)
                    solara.SliderFloat("", value=dfRBase_roundtime, min=0, max=60)
                    # with solara.Columns([1,9]):
                    with solara.Columns([3,2,1]):
                        with solara.Column():
                            solara.InputInt(BR_language_dict.value.get('roundslot','格子数'), value=dfRBase_roundslots, continuous_update=True)
                            solara.SliderInt("", value=dfRBase_roundslots, min=0, max=63)
                        solara.InputInt(BR_language_dict.value.get('roundslotchange','格子数变化'), value=dfRBase_modifyslot)
                        def AddSlots(**kwargs):
                            if dfRBase_modifyslot.value!=0:
                                dfRBase_roundslots.value+=dfRBase_modifyslot.value
                        solara.Button(BR_language_dict.value.get('slotchange',"更新格子数"), on_click=AddSlots)
                        
                    with solara.Row():
                        solara.Checkbox(label=BR_language_dict.value.get('roundwin','是否胜利'), value=dfRBase_roundwin)
                        solara.ToggleButtonsSingle(value=dfRBase_roundclassname, values=classlist)#,label=classname)
                        solara.InputInt(BR_language_dict.value.get('roundranknum','对局id'), value=dfRBase_gameid, continuous_update=True)
                    with solara.Columns([1,1]):
                        with solara.Column():
                            solara.Select(label=BR_language_dict.value.get('roundrank','分段'), value=dfRBase_roundrank, values=rank_list_zh)
                        with solara.Column():
                            solara.InputInt(BR_language_dict.value.get('roundranknum','分段值'), value=dfRBase_roundranknum, continuous_update=True)
                            solara.SliderInt("", value=dfRBase_roundranknum, min=0, max=100)
                    # solara.SliderInt("", value=dfRBase_roundranknum, min=0, max=100)
                    with solara.Row():
                        solara.Button(BR_language_dict.value.get('save_roundinfo',"保存回合情况"), on_click=AddRoundInfo)
                        solara.Button(BR_language_dict.value.get('save_roundinfo',"开始新的一局"), on_click=NewRoundInfo)
                    solara.Markdown(f"当前的对局id{dfRBase_gameid.value}")
                with solara.Column():
                    solara.DataFrame(display_Gameinfo.value)#,items_per_page=10)
        # with solara.lab.Tab(BR_language_dict.value.get('roundbaseinfo','记录对局情况')):
            
        with solara.lab.Tab(language_dict.value.get('UI_ShopTab','商店道具分析')):
            BPB_Analyze()
        with solara.lab.Tab(language_dict.value.get('UI_GalaryTab','画廊和数据下载')):
            solara.Markdown(UI_setting_text.value)
            with solara.Row():
                file_object = dfroundbattleinfo.to_csv(index=False)
                solara.FileDownload(file_object,label='导出战斗数据', filename='battleinfo.csv',string_encoding = "utf-8-sig")
                file_object = dfroundbaseinfo.to_csv(index=False)
                solara.FileDownload(file_object,label='导出对局数据', filename='roundinfo.csv',string_encoding = "utf-8-sig")
                # with pd.ExcelWriter('analyze_data.xlsx') as writer:
                # # writer = pd.ExcelWriter('analyze_data.xlsx', engine='xlsxwriter')
                #     dfroundbattleinfo.to_excel(writer, sheet_name='battleinfo', index=False)
                #     dfroundbaseinfo.to_excel(writer, sheet_name='roundinfo', index=False)
                # solara.FileDownload('analyze_data.xlsx',label='导出完整数据', filename='analyze_data.xlsx')#,string_encoding = "utf-8-sig")
                with solara.Card(title="上传战斗数据"):
                    solara.FileDrop(
                        label="拖动到此上传，仅支持csv和excel文件",
                        on_file=lambda file_info: handle_file(file_info, dfroundbattleinfo),
                        lazy=False,  # We will only read the first 100 bytes
                    )        
                with solara.Card(title="上传对局数据"):
                    solara.FileDrop(
                        label="拖动到此上传，仅支持csv和excel文件",
                        on_file=lambda file_info: handle_file(file_info, dfroundbaseinfo),
                        lazy=False,  # We will only read the first 100 bytes
                    )
            image_folder_path='Image/'
            imagelist=['art_Reaper','art_Pyromancer','art_Berserker','art_Ranger']
            videotitle_list=['彩虹女巫锅','6百冰冰法彩黏','2万甲白狼头领战','一瞬千击！大象匕首战']
            videourl_list=['https://www.bilibili.com/video/BV18w4m197BW','https://www.bilibili.com/video/BV1QH4y1A7jD','https://www.bilibili.com/video/BV12Z421n75G','https://www.bilibili.com/video/BV1ST421S7Ym']
            totalinfo=zip(imagelist,videotitle_list,videourl_list)
            
            with solara.GridFixed(columns=4, align_items="end", justify_items="stretch"):

                for detail_image,detail_title,detail_url in totalinfo:
                    with solara.Div():
                        solara.Image(image_folder_path+detail_image+'.png')
                        # solara.Text(detail_title)
                        if detail_url!='':
                            solara.Button(label=f"观看视频：{detail_title}", icon_name="mdi-file-video", attributes={"href": detail_url, "target": "_blank"}, text=True, outlined=True) 
                            
                # for art in imagelist:
                #     with solara.Div():
                #         solara.Image(art+'.png')
                #         solara.Text(art)
                        
                # with solara.Div():
                #     image_url = r"https://i0.hdslb.com/bfs/archive/03c147dc31bb93d432ce2bfb29ee4e7e6008c63f.jpg"
                #     solara.Image(image_url)
                #     solara.Text(art)
                #     link_url = "https://www.bilibili.com/video/BV12Z421n75G/"
                #     solara.Button(label="查看视频", icon_name="mdi-github-circle", attributes={"href": link_url, "target": "_blank"}, text=True, outlined=True) 
                    # solara.Link(link_url, image_url)
            #除了imagelist以外，怎样可以做到获取一个动态数据（那就要结合notion和token了）
        if Record_initialing.value:
            # print('检测执行情况')

            set_roundinfo(latestround)            
            dfRBI=RecalUIDataFrame(dfroundbattleinfo,False)
            # print(dfRBI)
            UpdateGraphic(dfRBI.copy())
            UpdateUIDataFrame(dfRBI.copy())
            
            #更新画图，记录也执行一次显示出表头？
            Record_initialing.value=False
        with solara.lab.Tab(language_dict.value.get('UI_ContactTab','和我联系')):
            Contact_Me()
# BPB_Record

@solara.component
def Page():
    BPB_Record()

Page()