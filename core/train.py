from core.feature import *
from core.check import *
from core.predict import *
import fire







def predict_wtid(wtid):
    block_list = get_blocks()

    train_ex = get_train_ex(wtid)
    for blockid, missing_block in block_list.loc[
                (block_list.wtid == wtid) &
                (block_list.kind == 'missing')
                #( block_list.col == 'var001')
                    ].iterrows():
        col_name = missing_block.col


        para = get_best_para(col_name, None, top_n=0)

        logger.info(f'===Predict wtid:{wtid:2},{col_name},blockid:{blockid:6}, best_file_num:{para.file_num}, type:{missing_block.data_type}')
        train, sub = get_submit_feature_by_block_id(blockid, para)

        predict_fn = get_predict_fun(blockid, train, para)
        predict_res = predict_fn(sub.iloc[:, 1:])
        logger.debug(f'sub={sub.shape}, predict_res={predict_res.shape}, type={type(predict_res)}')
        sub[col_name] = predict_res

        begin, end = missing_block.begin, missing_block.end

        logger.debug(
            f'train.loc[begin:end,col_name] = {train_ex.loc[begin:end,col_name].shape}, predict_res:{predict_res.shape}, {begin}, {end}, {wtid}, {col_name}')
        train_ex.loc[begin:end, col_name] = predict_res
        logger.debug(f'wtid:{wtid},col:{missing_block.col}, blockid:{blockid},train_ex:{train_ex.shape}, train:{train.shape}')

    submit = get_sub_template()
    submit = submit.loc[submit.wtid==wtid]
    submit.ts = pd.to_datetime(submit.ts)
    train_ex = train_ex[ train_ex.ts.isin(submit.ts) ]
    train_ex.wtid = train_ex.wtid.astype(int)
    train_ex = train_ex.drop(axis=['column'], columns=['time_sn'])
    return convert_enum(train_ex)

@file_cache(overwrite=True)
def predict_all(version):
    args = options()

    score_df = check_score_all(pic=False)
    score_avg = round(score_df.iloc[:, -5].mean(), 4), round(score_df.iloc[:, -5:].max(axis=1).mean(), 4)
    score_avg = [ str(item) for  item in score_avg]
    logger.info(f'The validate score is {score_avg} for args:{args}')


    train_list = []
    from tqdm import tqdm
    for wtid in tqdm(range(1, 34)):
        train_ex =  predict_wtid(wtid, args)
        #train_ex = train_ex.set_index(['ts', 'wtid'])
        train_list.append(train_ex)
    train_all = pd.concat(train_list)#.set_index(['ts', 'wtid'])


    submit = get_sub_template()
    submit.ts = pd.to_datetime(submit.ts)
    submit = submit[['ts', 'wtid']].merge(train_all, how='left', on=['ts', 'wtid'])
    submit = round(submit, 2)

    file = f"./output/submit_{args}_score={'_'.join(score_avg)}.csv"
    submit = submit.iloc[:, :70]
    file = replace_invalid_filename_char(file)
    submit.to_csv(file,index=None)

    logger.info(f'Sub({submit.shape}) file save to {file}')

    return submit





if __name__ == '__main__':
    """
    python core/train.py predict_wtid 1

    """
    #fire.Fire()

    # score_df = check_score_all(version='0126')



    logger.info(f'Program input:{options()}')
    sub = predict_wtid(2)

    logger.info(sub.shape)

    #submit = predict_all(options().version)
    #
    # score_df = check_score_all(pic=False)
    # score_avg = round(score_df.iloc[:, -5].mean(), 4), round(score_df.iloc[:, -5:].max(axis=1).mean(), 4)
    # score_avg = [ str(item) for  item in score_avg]
    # logger.info(f'The validate score is {score_avg} for args:{options()}')
    #
    # file = f'./output/score_{options()}_{score_avg}.h5'
    # file = replace_invalid_filename_char(file)
    # score_df.to_hdf(file, key='score')
    # logger.info(f'All socre is save to :{file}')


