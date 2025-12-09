


class BaseRatings:

    def get(self, item_id):
        raise NotImplementedError

    def inc(self, item_id,
            amount=1,):
        raise NotImplementedError

    def dec(self, item_id,
            amount=1,):
        raise NotImplementedError
