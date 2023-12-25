from __future__ import annotations

from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
from aiohttp import ClientSession
from commbank_api_client.types import Account, Transaction
from datetime import datetime


async def create_client(username: str, password: str) -> Client:
    instance = Client(username, password)
    await instance._login()
    return instance


class Client:
    _headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/104.0.5112.79 Safari/537.36'}

    def _parse_form(self, form: Tag | NavigableString | None):
        filtered = filter(lambda x: x.has_attr("value") and x['value'] is not None, form.find_all('input'))
        kv_list = map(lambda x: (x["name"], x["value"]), filtered)
        return {x[0]: x[1] for x in kv_list}

    def __init__(self, username: str, password: str):
        self._session = ClientSession()
        self._paging = {}
        self._username = username
        self._password = password

    async def __aenter__(self):
        await self._login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()

    async def close(self):
        await self._session.close()

    async def _login(self):
        init_get = await self._session.get("https://www.my.commbank.com.au/netbank/Logon/Logon.aspx",
                                           headers=self._headers)
        init_get_soup = BeautifulSoup(await init_get.text(), 'html.parser')
        dict_payload = self._parse_form(init_get_soup.find("form", {"id": "form1"}))
        dict_payload['JS'] = 'E'
        dict_payload['txtMyClientNumber$field'] = self._username
        dict_payload['txtMyPassword$field'] = self._password

        oidc = await self._session.post("https://www.my.commbank.com.au/netbank/Logon/Logon.aspx",
                                        headers=self._headers, data=dict_payload)
        oidc_soup = BeautifulSoup(await oidc.text(), 'html.parser')
        oidc_form = oidc_soup.find('form')
        url = oidc_form['action']
        if url != "https://www.commbank.com.au/retail/netbank/identity/signin-oidc":
            raise Exception("Unable to login")
        oidc_payload = self._parse_form(oidc_form)

        await self._session.post(url, headers=self._headers, data=oidc_payload)

    async def get_accounts(self) -> list[Account]:
        res = await self._session.get("https://www.commbank.com.au/retail/netbank/api/home/v1/accounts",
                                headers=self._headers)
        res_json = await res.json()
        return list(map(lambda x: Account(
            acc_number=x["number"],
            id=x["link"]["url"].replace("/retail/netbank/accounts/?account=", ""),
            name=x["displayName"],
            balance=float(x["balance"][0]["amount"]),
            funds=float(x["availableFunds"][0]["amount"]),
            currency=x["balance"][0]["currency"]
        ), res_json['accounts']))

    async def _get_paging_key(self, acc_id: str, page: int) -> str:
        if page in self._paging:
            return self._paging[page]
        else:
            if len(self._paging.items()) == 0:
                res = await self._session.get(f"https://www.commbank.com.au/retail/netbank/accounts/api"
                                                    f"/transactions?account={acc_id}")
                res_json = await res.json()
                self._paging[1] = res_json["pagingKey"]
            last_page, last_page_key = max(self._paging.items(), key=lambda x: x[0])
            for i in range(page - last_page):
                res = await self._session.get(f"https://www.commbank.com.au/retail/netbank/accounts/api"
                                                  f"/transactions?account={acc_id}&pagingKey={last_page_key}",
                                                  headers=self._headers)
                res_json = await res.json()
                last_page_key = res_json["pagingKey"]
                self._paging[last_page + i + 1] = last_page_key
            return self._paging[page]

    async def get_transactions(self, acc_id: str, page: int = 1):
        paging_query_arg = "&pagingKey=" + await self._get_paging_key(acc_id, page) if page > 1 else ""
        res = await self._session.get(
            f"https://www.commbank.com.au/retail/netbank/accounts/api/transactions?account={acc_id}{paging_query_arg}",
            headers=self._headers)
        res_json = await res.json()
        self._paging[page + 1] = res_json["pagingKey"]

        pending_transactions = list(map(lambda x: Transaction(
            id=None,
            transaction_details_request=x["transactionDetailsRequest"],
            description=x["description"],
            created=datetime.strptime(x["createdDate"], "%Y-%m-%dT%H:%M:%S"),
            amount=float(x["amount"]),
            pending=True
        ), res_json["pendingTransactions"])) if "pendingTransactions" in res_json else []
        transactions = list(map(lambda x: Transaction(
            id=x["transactionId"],
            transaction_details_request=None,
            description=x["description"],
            created=datetime.strptime(x["createdDate"], "%Y-%m-%dT%H:%M:%S"),
            amount=float(x["amount"]),
            pending=False
        ), res_json["transactions"])) + pending_transactions
        return sorted(transactions, key=lambda x: x.created, reverse=True)
