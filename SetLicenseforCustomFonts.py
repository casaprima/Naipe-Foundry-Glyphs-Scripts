# MenuTitle: Set License for Custom Fonts
# -*- coding: utf-8 -*-
__doc__="""
Sets License and Trademark property with dynamic placeholders for Custom Fonts
"""

from vanilla import Window, EditText, TextBox, Button
from GlyphsApp import Glyphs, Message
import re

# --- Retrieve last used client name from Glyphs defaults ---
last_client_name = Glyphs.defaults["com.naipe.SetLicenseLastClientName"] or ""

# --- Window dimensions ---
w = Window((380, 170), "📝 Set License for Custom Fonts")

# --- Instructions ---
w.instruction = TextBox(
    (10, 10, -10, 40),
    "⚠️ Make sure to input the client's full legal name."
)

# --- Client name input ---
w.client_name_input = EditText((10, 60, -10, 22), last_client_name)

# --- OK button callback ---
def okCallback(sender):
    client_name = w.client_name_input.get().strip()

    if not client_name:
        Message("❌ Missing Client Name", "Please enter the client's full legal name.")
        return

    # Save the client name for next run
    Glyphs.defaults["com.naipe.SetLicenseLastClientName"] = client_name

    font = Glyphs.font
    if not font:
        Message("❌ No Font Open", "Please open a font before running this script.")
        return

    # --- Filter Family Name ---
    family_name = font.familyName or ""
    family_name = re.sub(
        r'\s*(beta\s*\d*|alpha)$',
        '',
        family_name,
        flags=re.IGNORECASE
    ).strip()

    # --- License texts ---
    license_texts = {
        "English": f"""When using the {family_name} fonts, you agree to use them exclusively in branding and communication materials related to {client_name} and are not authorized to use it for any other purpose.

Modifying, adapting, altering, converting, translating, or otherwise modifying the {family_name} font software is not permitted without written authorisation from Naipe Foundry.

Sending or sharing the {family_name} fonts with anyone or any organisation, or any third party that has not been directly contracted by {client_name} as a supplier, partner, franchisee, contractor, or otherwise associated, is not allowed.""",

        "Portuguese": f"""Ao utilizar as fontes digitais {family_name}, você aceita usá-las exclusivamente em materiais de marca e comunicação relacionados à {client_name} e reconhece que não está autorizado a usá-las para nenhum outro propósito.

Não é permitido modificar, adaptar, alterar, converter, traduzir ou de qualquer outra forma modificar o software da fonte digital {family_name} sem autorização por escrito da Naipe Foundry.

Não é permitido enviar ou compartilhar as fontes {family_name} com qualquer pessoa ou organização, ou com qualquer terceiro que não tenha sido contratado diretamente pela {client_name} como fornecedor, parceiro, franqueado, contratado ou de qualquer outra forma associado.""",

        "Spanish": f"""Al utilizar las tipografías digitales {family_name}, aceptas utilizarlas exclusivamente en materiales de marca y comunicación relacionados con el {client_name} y que no estás autorizado a utilizarlas para ningún otro propósito.

No se permite modificar, adaptar, alterar, convertir, traducir o de cualquier otra manera modificar el software de tipografía digital {family_name} sin la autorización por escrito de Naipe Foundry.

No está permitido enviar o compartir las fuentes {family_name} con ninguna persona u organización, o cualquier tercero que no haya sido contratado directamente por {client_name} como proveedor, socio, franquiciado, contratista o de cualquier otra manera asociado."""
    }

    # --- Set License (localized) ---
    # Localized license text lives under the "licenses" property, with one
    # sub-value per language tag: "dflt" (English/default), "PTG" (Portuguese),
    # "ESP" (Spanish). Clear any existing entries first so old languages or
    # stale text don't linger, then write fresh values for all three.
    for prop in list(font.properties):
        if prop.key == "licenses":
            font.properties.remove(prop)

    font.setProperty_value_languageTag_("licenses", license_texts["English"], "dflt")
    font.setProperty_value_languageTag_("licenses", license_texts["Portuguese"], "PTG")
    font.setProperty_value_languageTag_("licenses", license_texts["Spanish"], "ESP")


    # --- Set Trademark ---
    font.trademark = f"{family_name} is a trademark of Naipe Foundry. All rights reserved."

    Glyphs.showNotification(
        "✅ Font Info Updated",
        "Licenses overwritten and Trademark set successfully."
    )

    w.close()

# --- OK button ---
w.okButton = Button(
    (125, 100, 140, 30),
    "✅ Apply License",
    callback=okCallback
)

# --- Disclaimer ---
w.disclaimer = TextBox(
    (10, 135, -10, 20),
    "ℹ️ Existing licenses will be overwritten.",
    sizeStyle="small"
)

# --- Open the window ---
w.open()