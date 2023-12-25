from commbank_api_client import create_client, Client
import asyncio


async def main():
    # initiate client without async context manager and log in
    # client = await create_client("username", "password")
    # Client must be closed manually to avoid resource leak
    # await client.close()

    # Initiate client with async context manager and log in (recommended)
    async with Client("username", "password") as client:
        # get account ID
        account_id = (await client.get_accounts())[0].id

        # get transactions (first page)
        transactions = await client.get_transactions(account_id)

        # get transactions (second page)
        transactions2 = await client.get_transactions(account_id, page=2)

asyncio.run(main())
