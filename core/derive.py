from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes


def address(mnemonic: str, index: int = 0) -> str:
    seed = Bip39SeedGenerator(mnemonic).Generate()
    acct = (
        Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
        .Purpose()
        .Coin()
        .Account(0)
        .Change(Bip44Changes.CHAIN_EXT)
    )
    return acct.AddressIndex(index).PublicKey().ToAddress()
