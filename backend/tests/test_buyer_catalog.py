import unittest

from app.buyer_catalog import _cnpj_valid, _unit


class BuyerCatalogValidationTests(unittest.TestCase):
    def test_known_numeric_cnpjs(self):
        self.assertTrue(_cnpj_valid("00394502000144"))
        self.assertTrue(_cnpj_valid("14100747000126"))

    def test_invalid_check_digit_is_rejected(self):
        self.assertFalse(_cnpj_valid("00394502000145"))

    def test_invalid_format_is_rejected(self):
        self.assertFalse(_cnpj_valid("123"))
        self.assertFalse(_cnpj_valid("00000000000000"))

    def test_unit_uses_raw_pncp_fields(self):
        unit = _unit({
            "unidadeOrgao": {
                "codigoUnidade": "1838",
                "nomeUnidade": "Prefeitura Municipal",
                "ufSigla": "BA",
                "municipioNome": "Riachão das Neves",
                "codigoIbge": "2926202",
            }
        })
        self.assertEqual(unit["code"], "1838")
        self.assertEqual(unit["uf"], "BA")
        self.assertEqual(unit["codigo_ibge"], "2926202")

    def test_missing_unit_is_preserved_as_missing(self):
        self.assertIsNone(_unit({"unidadeOrgao": None}))


if __name__ == "__main__":
    unittest.main()
