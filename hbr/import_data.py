import requests
import re
import akshare as ak
import pandas as pd
import datetime

class MARKET:
    SH = 'SH'
    SZ = 'SZ'
    BJ = 'BJ'
    

g_market_list = [MARKET.SH, MARKET.SZ, MARKET.BJ]


class MARKETID:
    SH = 1
    SZ = 2
    BJ = 3


class STOCKTYPE:
    BLOCK = 0 # 板块
    A = 1 # A股
    INDEX = 2 # 指数
    B = 3 # B股
    FUND = 4 # 基金（非ETF）
    ETF = 5 # ETF
    ND = 6 # 国债
    BOND = 7 # 其他债券
    GEM = 8 # 创业板
    START = 9 # 科创板
    A_BJ = 11 # 北交所A股


def get_a_stktype_list():
    """获取A股市场证券类型元组，含B股"""
    return(STOCKTYPE.A, STOCKTYPE.INDEX, STOCKTYPE.B, STOCKTYPE.GEM, STOCKTYPE.START, STOCKTYPE.A_BJ)


def get_stktype_list(quotations=None):
    """根据行情类别获取股票类别元组

    Args:
        quotations (_type_, optional): _description_. Defaults to None.
        :param quotations: 'stock' (股票) | 'fund' （基金） | 'bond' （债券）
        :rtype: tuple
        :return: 股票类别元组
    """
    if not quotations:
        return (1, 2, 3, 4, 5, 6,7, 7, 9, 11)
    
    result = []
    for quotation in quotations:
        new_quotation = quotation.lower()
        if new_quotation == 'stock':
            result += list(get_a_stktype_list())
        elif new_quotation == 'fund':
            result += [STOCKTYPE.FUND, STOCKTYPE.ETF]
        elif new_quotation == 'bond':
            result += [STOCKTYPE.ND, STOCKTYPE.BOND]
        else:
            print('Unknown quotation: {}'.format(quotation))
            
    return tuple(result)

# @hku_catch(ret=[], trace=True)
# @timeout(120)
def get_stk_code_name_list(market:str) -> list: # type: ignore
    # 获取深圳股票代码
    if market == MARKET.SZ:
        ind_list = ["A股列表", "B股列表"]
        df = None
        for ind in ind_list:
            tmp_df = ak.stock_info_sz_name_code(ind)
            tmp_df.rename(columns={'A股代码': 'code', 'A股简称': 'name'}, inplace=True)
            df = pd.concat([df, tmp_df]) if df is not None else tmp_df
        # hku_info("获取深圳证券交易所股票数量: {}", len(df) if df is not None else 0)
        return df[['code', 'name']].to_dict(orient='records') if df is not None else []
    
    # 获取上海股票代码
    if market == MARKET.SH:
        ind_list = ["主板A股", "主板B股", '科创板']
        df = None
        for ind in ind_list:
            tmp_df = ak.stock_info_sh_name_code(ind)
            tmp_df.rename(columns={'A股代码': 'code', 'A股简称': 'name'}, inplace=True)
            df = pd.concat([df, tmp_df]) if df is not None else tmp_df
        # hku_info("获取上海证券交易所股票数量: {}", len(df) if df is not None else 0)
        return df[['code', 'name']].to_dict(orient='records') if df is not None else []
    
    # 获取北京股票代码
    if market == MARKET.BJ:
        df = ak.stock_info_bj_name_code()
        df.rename(columns={'A股代码': 'code', 'A股简称': 'name'}, inplace=True)
        # hku_info("获取北京证券交易所股票数量: {}", len(df) if df is not None else 0)
        return df[['code', 'name']].to_dict(orient='records') if df is not None else []
    

# @hku_catch(ret=[], trace=True)
# @timeout(120)
def get_index_code_name_list() -> list:
    """
    获取所有股票指数代码名称列表
    从新浪获取,多次频繁调用会被封禁IP,需10分钟后再试

    Returns:
        [{'market_code': 'SHxxx'}, ...]
    """
    if hasattr(ak, 'stock_zh_index_spot_sina'):
        df = ak.stock_zh_index_spot_sina()
    elif hasattr(ak, 'stock_zh_index_spot_em'):
        df = ak.stock_zh_index_spot_em
    else:
        df = ak.stock_zh_index_spot()
        pass
    res = [{'market_codce': df.loc[i]['代码'].upper(), 'name': df.loc[i]['名称']} for i in range(len(df))]
    ret = [v for v in res if len(v['market_code']) == 8]
    return ret
    

g_fund_code_name_list = {}
for market in g_market_list:
    g_fund_code_name_list[market] = []
    pass
g_last_get_fund_code_name_list_date = datetime.date(1990, 12, 0)


# @hku_catch(ret=[], trace=True)
# @timeout(60)
def get_fund_code_name_list(market:str) -> list:
    pass
