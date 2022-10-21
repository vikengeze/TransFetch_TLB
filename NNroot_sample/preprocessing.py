import config as cf
import logging
import numpy as np
import pandas as pd
import torch
import pdb
import lzma
import itertools
from tqdm import tqdm
import os
import math

#%% Preprocessing
#%%%
BLOCK_BITS=cf.BLOCK_BITS
TOTAL_BITS=cf.TOTAL_BITS
LOOK_BACK=cf.LOOK_BACK
PRED_FORWARD=cf.PRED_FORWARD

BLOCK_NUM_BITS=cf.BLOCK_NUM_BITS
PAGE_BITS=cf.PAGE_BITS
BITMAP_SIZE=cf.BITMAP_SIZE
DELTA_BOUND=cf.DELTA_BOUND
SPLIT_BITS=cf.SPLIT_BITS
FILTER_SIZE=cf.FILTER_SIZE

#%%% Interface

def read_load_trace_data(load_trace, num_prefetch_warmup_instructions,num_total_instructions,skipping=1): #change skipping to 1=1M(warmup in traces)
    
    def process_line(line):
        split = line.strip().split(', ')
        return int(split[0]), int(split[1]), int(split[2], 16), int(split[3], 16), split[4] == '1'
    timeliness=9
    train_data = []
    eval_data = []
    if load_trace[-2:] == 'xz':
        with lzma.open(load_trace, 'rt') as f:
            lline_ids = [0]*timeliness
            for i in range(timeliness):
                lline_ids[i] = int((i*skipping*1000000)/timeliness)
            for line in f:
                pline = process_line(line)
                if pline[0]>skipping*1000000:
                    if pline[0] < num_prefetch_warmup_instructions * 1000000:
                        train_data.append([lline_ids.pop(0), pline[1], pline[2], pline[3], pline[4]])
                        lline_ids.append(pline[0])
                    else:
                        if pline[0] < num_total_instructions * 1000000:
                            eval_data.append([lline_ids.pop(0), pline[1], pline[2], pline[3], pline[4]])
                            lline_ids.append(pline[0])
                        else:
                            break
    else:
        with open(load_trace, 'r') as f:
            lline_ids = [0]*timeliness
            for i in range(timeliness):
                lline_ids[i] = int((i*skipping*1000000)/timeliness)
            for line in f:
                pline = process_line(line)
                if pline[0]>skipping*1000000:
                    if pline[0] < num_prefetch_warmup_instructions * 1000000:
                        train_data.append([lline_ids.pop(0), pline[1], pline[2], pline[3], pline[4]])
                        lline_ids.append(pline[0])
                    else:
                        if pline[0] < num_total_instructions * 1000000:
                            eval_data.append([lline_ids.pop(0), pline[1], pline[2], pline[3], pline[4]])
                            lline_ids.append(pline[0])
                        else:
                            break

    return train_data, eval_data

def read_load_trace_data_gen(load_trace, num_prefetch_warmup_instructions,num_total_instructions,skipping=1): #change skipping to 1=1M(warmup in traces)
    
    def process_line(line):
        split = line.strip().split(', ')
        return int(split[0]), int(split[1]), int(split[2], 16), int(split[3], 16), split[4] == '1'
    timeliness=9
    train_data = []
    eval_data = []
    if load_trace[-2:] == 'xz':
        with lzma.open(load_trace, 'rt') as f:
            lline_ids = [0]*timeliness
            for i in range(timeliness):
                lline_ids[i] = int((i*skipping*1000000)/timeliness)
            for line in f:
                pline = process_line(line)
                if pline[0]>skipping*1000000:
                    if pline[0] < num_prefetch_warmup_instructions * 1000000:
                        train_data.append([lline_ids.pop(0), pline[1], pline[2], pline[3], pline[4]])
                        lline_ids.append(pline[0])
                    else:
                        if pline[0] < num_total_instructions * 1000000:
                            eval_data.append([lline_ids.pop(0), pline[1], pline[2], pline[3], pline[4]])
                            lline_ids.append(pline[0])
                        else:
                            break
    else:
        with open(load_trace, 'r') as f:
            lline_ids = [0]*timeliness
            for i in range(timeliness):
                lline_ids[i] = int((i*skipping*1000000)/timeliness)
            for line in f:
                pline = process_line(line)
                if pline[0]>skipping*1000000:
                    if pline[0] < num_prefetch_warmup_instructions * 1000000:
                        train_data.append([lline_ids.pop(0), pline[1], pline[2], pline[3], pline[4]])
                        lline_ids.append(pline[0])
                    else:
                        if pline[0] < num_total_instructions * 1000000:
                            eval_data.append([lline_ids.pop(0), pline[1], pline[2], pline[3], pline[4]])
                            lline_ids.append(pline[0])
                        else:
                            break

    return train_data, eval_data  

def convert_to_binary(data,bit_size=64-6):
    get_bin = lambda x, n: format(x, 'b').zfill(n)
    res=get_bin(data,bit_size)
    return [int(char)+OFFSET for char in res]
    # make it (1,2)

#bitmap(1,2)

def to_bitmap(n,bitmap_size): 
    #l0=np.ones((bitmap_size),dtype = int)
    l0=np.zeros((bitmap_size),dtype = int)
    if(len(n)>0):
        for x in n:
            if x>0:
                l0[int(x)-1]=1
            elif x<0:
                l0[int(x)]=1
        l1=list(l0)
        return l1
    else:
        return list(l0)

def split_to_words(value,BN_bits=58,split_bits=6,norm=True):
    #res=[SPLITER_ID]
    res=[]
    for i in range(BN_bits//split_bits+1):
        divider=2**split_bits
        #res.append(value%(divider)+OFFSET)#add 1, range(1-64),0 as padding
        new_val=value%(divider)
        if norm==True:
            new_val=new_val/divider
        res.append(new_val)#
        value=value//divider
    return res

def delta_acc_list(delta,DELTA_BOUND=128):#delta accumulative list
    res=list(itertools.accumulate(delta))
    res=[i for i in res if abs(i)<=DELTA_BOUND]
    if len(res)==0:
        res="nan"
    return res


def addr_hash(x,HASH_BITS):
    t = int(x)^(int(x)>>32); 
    result = (t^(t>>HASH_BITS)) & (2**HASH_BITS-1); 
    return result/(2**HASH_BITS)

def ip_list_norm(ip_list,HASH_BITS):
    return [addr_hash(ip,HASH_BITS) for ip in ip_list]

def page_list_norm(page_list,current_page):
    return list(1/(abs(np.array(page_list)-current_page)+1))
     
    
def preprocessing(data):
    print("preprocessing with context")
    df=pd.DataFrame(data)
    df.columns=["id", "cycle", "page_address", "ip", "hit"]
    df['page_address_delta']=df['page_address'].diff()


    '''
    df['raw']=df['addr']
    df['block_address'] = [x>>BLOCK_BITS for x in df['raw']]
    df['page_address'] = [ x >> PAGE_BITS for x in df['raw']]
    #df['page_address_str'] = [ "%d" % x for x in df['page_address']]
    df['page_offset'] = [x- (x >> PAGE_BITS<<PAGE_BITS) for x in df['raw']]
    df['block_index'] = [int(x>> BLOCK_BITS) for x in df['page_offset']]  
    #df["block_address_bin"]=df.apply(lambda x: convert_to_binary(x['block_address'],BLOCK_NUM_BITS),axis=1)
    df['block_addr_delta']=df['block_address'].diff()'''
    
    df['patch']=df.apply(lambda x: split_to_words(x['page_address'],BLOCK_NUM_BITS,SPLIT_BITS),axis=1)
    # past
    for i in range(LOOK_BACK):
        df['patch_past_%d'%(i+1)]=df['patch'].shift(periods=(i+1))
        df['ip_past_%d'%(i+1)]=df['ip'].shift(periods=(i+1))
        df['page_past_%d'%(i+1)]=df['page_address'].shift(periods=(i+1))
    
    #Pem, update, debug 2019/09/18
    past_name=['patch_past_%d'%(i) for i in range(LOOK_BACK,0,-1)]
    past_ip_name=['ip_past_%d'%(i) for i in range(LOOK_BACK,0,-1)]
    past_page_name=['page_past_%d'%(i) for i in range(LOOK_BACK,0,-1)]
    
    past_name.append('patch')
    past_ip_name.append('ip')
    past_page_name.append('page_address')
    #Pem, update done
    
    df["past"]=df[past_name].values.tolist()
    df["past_ip_abs"]=df[past_ip_name].values.tolist()
    df["past_page_abs"]=df[past_page_name].values.tolist()
    
    df=df.dropna() #drops N/A values
    
    df['past_ip']=df.apply(lambda x: ip_list_norm(x['past_ip_abs'],16),axis=1)
    df['past_page']=df.apply(lambda x: page_list_norm(x['past_page_abs'],x['page_address']),axis=1)
   
    
    #labels
    '''
    future_idx: delta to the prior addr
    future_delta: accumulative delta to current addr
    '''
    for i in range(PRED_FORWARD):
        df['delta_future_%d'%(i+1)]=df['page_address_delta'].shift(periods=-(i+1))
    
    for i in range(PRED_FORWARD):
            if i==0:
                df["future_idx"]=df[['delta_future_%d'%(i+1)]].values.astype(int).tolist()
            else:   
                #df["future_idx"] = df[['future_idx','delta_future_%d'%(i+1)]].values.astype(int).tolist()
                df["future_idx"]=np.hstack((df["future_idx"].values.tolist(), df[['delta_future_%d'%(i+1)]].values.astype(int))).tolist()
                
                #df[['delta_future_%d'%(i+1)]].values.tolist()
    
    #delta bitmap
    
    df["future_delta"]=df.apply(lambda x: delta_acc_list(x['future_idx'],DELTA_BOUND),axis=1)
    
    df=df[df["future_delta"]!="nan"]
    
    df["future"]=df.apply(lambda x: to_bitmap(x['future_delta'],BITMAP_SIZE),axis=1)
    df=df.dropna()

    np.random.seed(10)
    remove_n = math.floor(0.5 * len(df))
    drop_indices = np.random.choice(df.index, remove_n, replace=False)
    df = df.drop(drop_indices)

    return df[['id', 'cycle', 'page_address', 'ip', 'hit', 'page_address_delta', 'past', 'past_ip', 'past_page', 'future']]

def preprocessing_gen(data):
    print("preprocessing_gen with context")
    df=pd.DataFrame(data)
    df.columns=["id", "cycle", "page_address", "ip", "hit"]
    df['page_address_delta']=df['page_address'].diff()
    '''
    df['raw']=df['addr']
    df['block_address'] = [x>>BLOCK_BITS for x in df['raw']]
    df['page_address'] = [ x >> PAGE_BITS for x in df['raw']]
    #df['page_address_str'] = [ "%d" % x for x in df['page_address']]
    df['page_offset'] = [x- (x >> PAGE_BITS<<PAGE_BITS) for x in df['raw']]
    df['block_index'] = [int(x>> BLOCK_BITS) for x in df['page_offset']]  
    #df["block_address_bin"]=df.apply(lambda x: convert_to_binary(x['block_address'],BLOCK_NUM_BITS),axis=1)
    df['block_addr_delta']=df['block_address'].diff()'''
    
    df['patch']=df.apply(lambda x: split_to_words(x['page_address'],BLOCK_NUM_BITS,SPLIT_BITS),axis=1)
    # past
    
    for i in range(LOOK_BACK):
        df['patch_past_%d'%(i+1)]=df['patch'].shift(periods=(i+1))
        df['ip_past_%d'%(i+1)]=df['ip'].shift(periods=(i+1))
        df['page_past_%d'%(i+1)]=df['page_address'].shift(periods=(i+1))
    
    #Pem, update, debug 2019/09/18
    past_name=['patch_past_%d'%(i) for i in range(LOOK_BACK,0,-1)]
    past_ip_name=['ip_past_%d'%(i) for i in range(LOOK_BACK,0,-1)]
    past_page_name=['page_past_%d'%(i) for i in range(LOOK_BACK,0,-1)]
    
    past_name.append('patch')
    past_ip_name.append('ip')
    past_page_name.append('page_address')
    #Pem, update done
    
    df["past"]=df[past_name].values.tolist()
    df["past_ip_abs"]=df[past_ip_name].values.tolist()
    df["past_page_abs"]=df[past_page_name].values.tolist()
    
    df=df.dropna()
    df['past_ip']=df.apply(lambda x: ip_list_norm(x['past_ip_abs'],16),axis=1)
    df['past_page']=df.apply(lambda x: page_list_norm(x['past_page_abs'],x['page_address']),axis=1)

    return df[['id', 'cycle', 'page_address', 'ip', 'hit', 'page_address_delta', 'past', 'past_ip', 'past_page']]
