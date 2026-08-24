from dataclasses import dataclass

@dataclass(slots=True)
class AuctionUpdate:
    state: str
    event: str|None = None

class AuctionTracker:
    def __init__(self, acceptance_closes=2, poc_tolerance_atr=.05, rejection_penetration_atr=.03):
        self.acceptance_closes = acceptance_closes
        self.poc_tolerance_atr = poc_tolerance_atr
        self.rejection_penetration_atr = rejection_penetration_atr
        self.above_count = 0
        self.below_count = 0
        self.accepted_above = False
        self.accepted_below = False
        self.prev_close = None
        self.rejected_above_latched = False
        self.rejected_below_latched = False

    def reset(self):
        self.above_count = self.below_count = 0
        self.accepted_above = self.accepted_below = False
        self.prev_close = None
        self.rejected_above_latched = False
        self.rejected_below_latched = False

    def update(self, *, close, high, low, ref_poc, ref_vah, ref_val, atr):
        if any(x is None for x in (ref_poc, ref_vah, ref_val)):
            return AuctionUpdate('N/A')
        penetration = atr*self.rejection_penetration_atr
        poc_tol = atr*self.poc_tolerance_atr
        rejected_above = (high > ref_vah+penetration and close <= ref_vah) or (self.prev_close is not None and self.prev_close > ref_vah and close <= ref_vah)
        rejected_below = (low < ref_val-penetration and close >= ref_val) or (self.prev_close is not None and self.prev_close < ref_val and close >= ref_val)
        event = None
        if close > ref_vah:
            self.above_count += 1; self.below_count = 0
        elif close < ref_val:
            self.below_count += 1; self.above_count = 0
        else:
            self.above_count = self.below_count = 0
            self.accepted_above = self.accepted_below = False
        if close > ref_vah:
            self.rejected_above_latched = False
        if close < ref_val:
            self.rejected_below_latched = False
        if rejected_above:
            if not self.rejected_above_latched:
                event = 'REJ_ABOVE_VAH'
                self.rejected_above_latched = True
            self.accepted_above = False
        elif rejected_below:
            if not self.rejected_below_latched:
                event = 'REJ_BELOW_VAL'
                self.rejected_below_latched = True
            self.accepted_below = False
        elif self.above_count >= self.acceptance_closes and not self.accepted_above:
            self.accepted_above = True; self.accepted_below = False; event = 'ACC_ABOVE_VAH'
        elif self.below_count >= self.acceptance_closes and not self.accepted_below:
            self.accepted_below = True; self.accepted_above = False; event = 'ACC_BELOW_VAL'
        if rejected_above: state='REJECTED ABOVE VAH'
        elif rejected_below: state='REJECTED BELOW VAL'
        elif self.accepted_above: state='ACCEPTED ABOVE VAH'
        elif self.accepted_below: state='ACCEPTED BELOW VAL'
        elif abs(close-ref_poc)<=poc_tol and low<=ref_poc+poc_tol and high>=ref_poc-poc_tol: state='POC TEST'
        elif ref_val<=close<=ref_vah and self.prev_close is not None and ref_val<=self.prev_close<=ref_vah: state='ROTATION INSIDE VALUE'
        elif close>ref_vah: state='ABOVE VAH'
        elif close<ref_val: state='BELOW VAL'
        else: state='INSIDE VALUE'
        self.prev_close = close
        return AuctionUpdate(state, event)
