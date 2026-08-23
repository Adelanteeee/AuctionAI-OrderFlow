import math
import numpy as np
import pandas as pd
from .config import BacktestConfig
from .data import resample_ohlcv
from .delta import weighted_delta
from .profile import profile_levels
from .auction import AuctionTracker
from .absorption import absorption_score
from .divergence import confirmed_divergence_events
from .outcomes import evaluate_event
from .reporting import summarize_events
from .sessions import get_session_spec, session_membership


def _atr(bars: pd.DataFrame, length: int) -> pd.Series:
    pc=bars.close.shift(1)
    tr=pd.concat([(bars.high-bars.low),(bars.high-pc).abs(),(bars.low-pc).abs()],axis=1).max(axis=1)
    return tr.rolling(length,min_periods=1).mean()

def _direction(event_type):
    return 'bullish' if event_type in {'ACC_ABOVE_VAH','REJ_BELOW_VAL','STRONG_SELLING_ABSORPTION','STRONG_BULL_DIVERGENCE'} else 'bearish'

def _migration(ref, dev, threshold):
    if ref is None or dev is None or any(pd.isna(x) for x in (*ref,*dev)):
        return 'N/A','N/A'
    rp,rvh,rvl=ref; dp,dvh,dvl=dev
    width=max(rvh-rvl,1e-12); rc=(rvh+rvl)/2; dc=(dvh+dvl)/2
    shift=(dc-rc)/width
    overlaps=dvh>=rvl and dvl<=rvh
    vm='VALUE SHIFTING UP' if shift>=threshold else 'VALUE SHIFTING DOWN' if shift<=-threshold else 'VALUE OVERLAP' if overlaps else 'VALUE DISPLACED'
    tol=width*.05
    pm='POC RISING' if dp>rp+tol else 'POC FALLING' if dp<rp-tol else 'POC STABLE'
    return vm,pm

def run_backtest(one_minute: pd.DataFrame, cfg: BacktestConfig, symbol='DATASET'):
    bars=resample_ohlcv(one_minute,cfg.parent_timeframe).copy()
    bars['atr']=_atr(bars,cfg.atr_length)
    bars['relative_volume']=bars.volume/bars.volume.rolling(cfg.volume_sma,min_periods=1).mean()
    ds=[]; dps=[]
    for ts in bars.index:
        end=ts+pd.Timedelta(cfg.parent_timeframe)
        intr=one_minute[(one_minute.index>=ts)&(one_minute.index<end)]
        d,p,_=weighted_delta(intr,cfg.body_weight,cfg.close_weight,cfg.pressure_cap,cfg.min_tick)
        ds.append(d); dps.append(p)
    bars['delta']=ds; bars['delta_pct']=dps
    bars['cvd']=bars.delta.fillna(0).cumsum()
    bars['cvd_smooth']=bars.cvd.ewm(span=cfg.cvd_smoothing,adjust=False).mean()
    bars['cvd_bias']=np.where(bars.cvd_smooth.diff()>0,'RISING',np.where(bars.cvd_smooth.diff()<0,'FALLING','FLAT'))
    dates=pd.Series([x.date() for x in bars.index],index=bars.index)
    bars['daily_volume']=bars.groupby(dates).volume.cumsum()
    pace=[]; prev_curve={}; current_date=None; cur_curve={}
    for ts,row in bars.iterrows():
        d=ts.date(); key=(ts.hour,ts.minute)
        if current_date is None: current_date=d
        if d!=current_date:
            prev_curve=cur_curve; cur_curve={}; current_date=d
        cur_curve[key]=row.daily_volume
        pv=prev_curve.get(key)
        pace.append(row.daily_volume/pv*100 if pv else math.nan)
    bars['daily_volume_pace']=pace

    spec=get_session_spec(cfg.session_name)
    session_volume=[]; session_pace=[]; in_flags=[]
    prev_session_curve={}; cur_session_curve={}; cur_session_id=None; cumulative=0.0
    for ts,row in bars.iterrows():
        in_session, session_id, elapsed=session_membership(ts,spec)
        in_flags.append(in_session)
        if in_session:
            if cur_session_id is None or session_id != cur_session_id:
                if cur_session_id is not None:
                    prev_session_curve=cur_session_curve
                cur_session_curve={}; cumulative=0.0; cur_session_id=session_id
            cumulative += row.volume
            cur_session_curve[elapsed]=cumulative
            pv=prev_session_curve.get(elapsed)
            session_volume.append(cumulative)
            session_pace.append(cumulative/pv*100.0 if pv else math.nan)
        else:
            session_volume.append(math.nan); session_pace.append(math.nan)
    bars['in_session']=in_flags
    bars['session_volume']=session_volume
    bars['session_volume_pace']=session_pace
    effective=bars['session_volume_pace'].where(bars['session_volume_pace'].notna(),bars['daily_volume_pace'])
    bars['volume_pace_state']=np.where(effective>=cfg.pace_expand,'EXPANDING',np.where(effective<=cfg.pace_contract,'CONTRACTING','NORMAL'))

    tracker=AuctionTracker(cfg.acceptance_closes,cfg.poc_tolerance_atr,cfg.rejection_penetration_atr)
    events=[]; day_h=[]; day_l=[]; day_v=[]; prev_ref=None; cur_date=None
    session_h=[]; session_l=[]; session_v=[]; prev_session_ref=None; cur_session_profile_id=None
    ref_p=[]; ref_h=[]; ref_l=[]; dev_p=[]; dev_h=[]; dev_l=[]; states=[]; vms=[]; pms=[]; abs_scores=[]; abs_states=[]
    prev_sp=[]; prev_sh=[]; prev_sl=[]; dev_sp=[]; dev_sh=[]; dev_sl=[]
    for i,(ts,row) in enumerate(bars.iterrows()):
        d=ts.date()
        if cur_date is None: cur_date=d
        if d!=cur_date:
            if day_v:
                prev_ref=profile_levels(day_h,day_l,day_v,cfg.profile_rows,cfg.value_area_pct)
            day_h=[]; day_l=[]; day_v=[]; cur_date=d; tracker.reset()
        in_s, sess_id, _elapsed = session_membership(ts,spec)
        if in_s and (cur_session_profile_id is None or sess_id != cur_session_profile_id):
            if session_v:
                prev_session_ref=profile_levels(session_h,session_l,session_v,cfg.profile_rows,cfg.value_area_pct)
            session_h=[]; session_l=[]; session_v=[]; cur_session_profile_id=sess_id
        dev=profile_levels(day_h,day_l,day_v,cfg.profile_rows,cfg.value_area_pct) if day_v else None
        dev_session=profile_levels(session_h,session_l,session_v,cfg.profile_rows,cfg.value_area_pct) if session_v else None
        if prev_ref:
            rp,rvh,rvl=prev_ref
            au=tracker.update(close=row.close,high=row.high,low=row.low,ref_poc=rp,ref_vah=rvh,ref_val=rvl,atr=row.atr)
        else:
            rp=rvh=rvl=math.nan; au=type('A',(),{'state':'N/A','event':None})()
        vm,pm=_migration(prev_ref,dev,cfg.value_shift_threshold)
        br=max(row.high-row.low,cfg.min_tick); uw=(row.high-max(row.open,row.close))/br; lw=(min(row.open,row.close)-row.low)/br; cl=(row.close-row.low)/br
        high_result=abs(row.close-(bars.close.iloc[i-1] if i else row.close)) >= row.atr*cfg.result_threshold_atr
        score,side,astate=absorption_score(delta_pct=row.delta_pct,relative_volume=row.relative_volume,high_result=high_result,lower_wick_ratio=lw,upper_wick_ratio=uw,close_location=cl,min_delta_pct=cfg.absorption_min_delta_pct,high_vol_mult=cfg.high_volume_mult)
        ref_p.append(rp); ref_h.append(rvh); ref_l.append(rvl)
        if dev: dp,dvh,dvl=dev
        else: dp=dvh=dvl=math.nan
        dev_p.append(dp); dev_h.append(dvh); dev_l.append(dvl); states.append(au.state); vms.append(vm); pms.append(pm); abs_scores.append(score); abs_states.append(astate)
        if prev_session_ref: spp,svh,svl=prev_session_ref
        else: spp=svh=svl=math.nan
        if dev_session: dsp,dsvh,dsvl=dev_session
        else: dsp=dsvh=dsvl=math.nan
        prev_sp.append(spp); prev_sh.append(svh); prev_sl.append(svl); dev_sp.append(dsp); dev_sh.append(dsvh); dev_sl.append(dsvl)
        if au.event:
            events.append({'timestamp':ts,'event_type':au.event,'direction':_direction(au.event)})
        if astate=='STRONG SELLING ABSORPTION': events.append({'timestamp':ts,'event_type':'STRONG_SELLING_ABSORPTION','direction':'bullish'})
        if astate=='STRONG BUYING ABSORPTION': events.append({'timestamp':ts,'event_type':'STRONG_BUYING_ABSORPTION','direction':'bearish'})
        end=ts+pd.Timedelta(cfg.parent_timeframe)
        intr=one_minute[(one_minute.index>=ts)&(one_minute.index<end)]
        day_h.extend(intr.high.tolist()); day_l.extend(intr.low.tolist()); day_v.extend(intr.volume.tolist())
        if in_s:
            session_h.extend(intr.high.tolist()); session_l.extend(intr.low.tolist()); session_v.extend(intr.volume.tolist())
    bars['ref_poc']=ref_p; bars['ref_vah']=ref_h; bars['ref_val']=ref_l
    bars['dev_poc']=dev_p; bars['dev_vah']=dev_h; bars['dev_val']=dev_l
    bars['prev_session_poc']=prev_sp; bars['prev_session_vah']=prev_sh; bars['prev_session_val']=prev_sl
    bars['dev_session_poc']=dev_sp; bars['dev_session_vah']=dev_sh; bars['dev_session_val']=dev_sl
    bars['auction_state']=states; bars['value_migration']=vms; bars['poc_migration']=pms
    bars['absorption_score']=abs_scores; bars['absorption_state']=abs_states

    for de in confirmed_divergence_events(bars[['low','high','delta','cvd']],left=3,right=3): events.append(de)
    records=[]
    for k,e in enumerate(sorted(events,key=lambda x:x['timestamp']),1):
        ts=e['timestamp']; pos=bars.index.get_loc(ts)
        row=bars.iloc[pos]; future=bars.iloc[pos+1:pos+1+cfg.outcome_horizon]
        out=evaluate_event(entry_close=row.close,atr=row.atr,direction=e['direction'],future=future,threshold_atr=cfg.outcome_threshold_atr)
        rec={'event_id':f'E{k:06d}','timestamp':ts,'symbol':symbol,'parent_timeframe':cfg.parent_timeframe,'event_type':e['event_type'],'direction':e['direction'],'close':row.close,'atr':row.atr,'delta':row.delta,'delta_pct':row.delta_pct,'cvd':row.cvd,'cvd_bias':row.cvd_bias,'relative_volume':row.relative_volume,'daily_volume':row.daily_volume,'daily_volume_pace':row.daily_volume_pace,'session_volume':row.session_volume,'session_volume_pace':row.session_volume_pace,'volume_pace_state':row.volume_pace_state,'ref_poc':row.ref_poc,'ref_vah':row.ref_vah,'ref_val':row.ref_val,'dev_poc':row.dev_poc,'dev_vah':row.dev_vah,'dev_val':row.dev_val,'auction_state':row.auction_state,'value_migration':row.value_migration,'poc_migration':row.poc_migration,'absorption_score':row.absorption_score,'absorption_state':row.absorption_state,'pivot_timestamp':e.get('pivot_timestamp')}
        for h in (1,3,5):
            if pos+h < len(bars):
                move=bars.close.iloc[pos+h]-row.close
                signed=move if e['direction']=='bullish' else -move
                rec[f'dir_return_{h}']=signed/row.atr if row.atr else math.nan
            else: rec[f'dir_return_{h}']=math.nan
        rec.update(out); records.append(rec)
    events_df=pd.DataFrame(records)
    if events_df.empty:
        events_df=pd.DataFrame(columns=['event_id','timestamp','event_type','auction_state','delta_pct','mfe_atr','mae_atr','label','dir_return_1','dir_return_3','dir_return_5'])
    summary=summarize_events(events_df,min_samples=10)
    return events_df,summary,bars
