from ndn.types import InterestNack, InterestTimeout
from ndn.utils import gen_nonce

async def sequential_fetcher(app, name, start_block_id, end_block_id, **kwargs):
    """
    A generator to fetch data packets between
    "`name`/`start_block_id`" and "`name`/`end_block_id`"\ in sequence.

    :param app: NDNApp.
    :param name: NonStrictName. Name prefix of Data.
    :param start_block_id: int. The start segment number.
    :param end_block_id: int. The end segment number.
    :return: Yield ``(FormalName, MetaInfo, Content, RawPacket)`` tuples in order.
    """
    if name is None:
        return
    for seq in range(start_block_id, end_block_id + 1):
        int_name = name + "/" + str(seq)
        # Try up to 3 times per block id
        trial_times = 1
        while True:
            try:
                data_name, meta_info, content, data_bytes = await app.express_interest(
                    int_name,
                    need_raw_packet=True,
                    must_be_fresh=True,
                    can_be_prefix=False,
                    nonce=gen_nonce(),
                    **kwargs)
                yield data_name, meta_info, content, data_bytes
                break
            except (InterestNack, InterestTimeout):
                trial_times += 1
                if trial_times > 3:
                    return  # No hope. Quit
    return
