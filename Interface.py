# Standard library imports
import io
import json
import math
import sys

# Third-party imports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
import folium
from folium.plugins import Geocoder
import requests
from branca.element import Element
from scipy.optimize import fsolve

# Local module imports
from interfaceqt import Ui_MainWindow

# API_KEY = 'INSERT YOUR KEY'
BASE_URL = 'https://maps.googleapis.com/maps/api/elevation/json'


def extract_value(lat, long, area):
    # Define the URL with the provided parameters
    url = f'http://www.leb.esalq.usp.br/wolff/rv/resultado.php?lat={lat}&long={long}&area={area}'
    # Send a GET request to the URL
    response = requests.get(url)
    # Check if the request was successful
    if response.status_code == 200:
        # Split the HTML content by lines
        lines = response.text.split('\n')
        # Iterate through the lines to find the row with "Q7,10"
        for line in lines:
            if '7,10' in line:
                # Split the line by "</td>" to extract the values
                values = line.split('</td>')
                # The value you want is the last part of the line
                target_value = values[-2].split('>')[-1].strip()
                return target_value  # Return the extracted value
        else:
            return "Row with 'Q7,10' not found in the HTML content"
    else:
        return "Failed to retrieve the web page"


def perda_de_carga_Darcy_Weisbach(Q, D, L, rugosidade):
    g = 9.81  # Aceleração devido à gravidade (m/s²)
    # Cálculo do coeficiente de atrito de Darcy-Weisbach (f) usando a equação de Colebrook-White

    def colebrook_white(f):
        return 1 / (f ** 0.5) + 2.0 * 2.51 * L / (D * rugosidade) * f ** 0.5 - 2.0 * Q ** 2 / (g * D ** 5)

    f = fsolve(colebrook_white, 0.01)[0]
    # Cálculo da perda de carga
    Hf = (4 * f * L * Q ** 2) / (D * g)
    return Hf


# Função responsável pelo cálculo das distâncias, levando em consideração vários fatores.
def haversine_with_height(lath1, lonh1, alth1, lath2, lonh2, alth2):
    # Radius of the Earth in meters
    earth_radius = 6371000  # Approximately 6,371 km
    # Convert latitude and longitude from degrees to radians
    lath1 = math.radians(lath1)
    lonh1 = math.radians(lonh1)
    lath2 = math.radians(lath2)
    lonh2 = math.radians(lonh2)
    # Calculate differences in latitude, longitude, and altitude
    dlath = lath2 - lath1
    dlonh = lonh2 - lonh1
    dalth = alth2 - alth1
    # Haversine formula for distance calculation on the Earth's surface
    a = math.sin(dlath / 2) ** 2 + math.cos(lath1) * math.cos(lath2) * math.sin(dlonh / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = earth_radius * c
    # Add the height difference to the distance
    distance_with_height = math.sqrt(distance ** 2 + dalth ** 2)
    return distance_with_height


class WebEnginePage(QWebEnginePage):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        print(msg)  # Check js errors
        if 'coordinates' in msg:
            self.parent.handleConsoleMessage(msg)


class Tela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.web_view = QWebEngineView(self.ui.ContainerMapa)
        self.ui.pushButtonReservatorio.clicked.connect(self.handleButtonClickres)
        self.ui.pushButtonFonte.clicked.connect(self.handleButtonClickfon)
        self.ui.pushButtonPump.clicked.connect(self.handleButtonClickpump)
        self.ui.pushButtoncalcular.clicked.connect(self.handleButtonClickCalculo)
        self.ui.pushButton_2.clicked.connect(self.handleButtonClickCalculoFluxo)
        self.ui.pushButton_Flow.clicked.connect(self.handleButtonClickCalculoFLOW2)
        layout = QVBoxLayout(self.ui.ContainerMapa)
        layout.addWidget(self.web_view)
        self.ui.ContainerMapa.setLayout(layout)
        self.label = QtWidgets.QLabel()
        layout.addWidget(self.label)
        # Inicialização das variáveis em um nível superior
        self.lat = None
        self.lng = None
        self.latreser = None
        self.lngreser = None
        self.latfon = None
        self.lngfon = None
        self.elevationfonte = None
        self.elevationreservatorio = None
        self.elevation = None
        self.deltaalturas = None
        self.latitude1 = None
        self.latitude2 = None
        self.longitute1 = None
        self.longitute2 = None
        self.d = None
        self.fluxomapa = None
        self.material_to_rugosity = {
            "Aço Comum": "0.045",
            "PVC (Policloreto de Vinila)": "0.01",
            "Ferro Fundido": "0.26",
            "Cobre": "0.01",
            "Aço Galvanizado": "0.045",
            "Polietileno (PE)": "0.001",
            "Polipropileno (PP)": "0.01",
            "CPVC (Cloreto de Polivinila Clorado)": "0.01",
            "PP-R (Polipropileno Copolímero Random)": "0.01",
            "ABS (Acrilonitrila Butadieno Estireno)": "0.01",
            "Pex (Polietileno Reticulado)": "0.001"
        }
        self.pump_flow = {
            "Aço Comum": "0.045",
        }
        coordinate = (-23.470049, -47.429751)
        self.m = folium.Map(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            zoom_start=15,
            name='Esri Satellite',
            location=coordinate)
        # Adicionar JS no mapa do Folium para capturar as coordenadas.
        self.m = self.add_customjs(self.m)
        Geocoder().add_to(self.m)
        # Armazenar mapa em um Objeto.
        data = io.BytesIO()
        self.m.save(data, close_file=False)
        # Inicio do Web Engine.
        webView = QWebEngineView()
        page = WebEnginePage(self)
        webView.setPage(page)
        webView.setHtml(data.getvalue().decode())  # html do folium map no Web Engine.
        layout.addWidget(webView)
        folium_map_html = self.m._repr_html_()
        self.web_view.setHtml(folium_map_html)

    def add_customjs(self, map_object):
        my_js = f"""{map_object.get_name()}.on("click",
                 function (e) {{
                    var data = `{{"coordinates": ${{JSON.stringify(e.latlng)}}}}`;
                    console.log(data)}});"""
        e = Element(my_js)
        html = map_object.get_root()
        html.script.get_root().render()
        # Insert new element or custom JS
        html.script._children[e.get_name()] = e
        return map_object

    def handleButtonClickCalculoFLOW2(self):
        try:

            try:
                vazao = float(self.ui.lineEditflow.text())
                if vazao < 15:
                    print("Vazão Insuficiente")
                    msg_box = QMessageBox(self)
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.setWindowTitle("Aviso")
                    msg_box.setText(
                        "A vazão é insuficiente para uma instalação de bombas carneiro, considere outra tecnologia.")
                    msg_box.exec_()
                    self.ui.lineEdit_FlowMax.setText("0")
                    self.ui.lineEdit_FlowMin.setText("0")
                    self.ui.lineEdit_Model.setText("Nenhum")
                    self.ui.lineEditTubIn.setText("Nenhum")
                    self.ui.lineEditTubOut.setText("Nenhum")
                elif vazao < 26:
                    print("Carneiro 3")
                    self.ui.lineEdit_FlowMax.setText("180")
                    self.ui.lineEdit_FlowMin.setText("72")
                    self.ui.lineEdit_Model.setText("Carneiro 3")
                    self.ui.lineEditTubIn.setText("1")
                    self.ui.lineEditTubOut.setText("1/2")
                elif vazao < 45:
                    print("Carneiro 4")
                    self.ui.lineEdit_FlowMax.setText("312")
                    self.ui.lineEdit_FlowMin.setText("125")
                    self.ui.lineEdit_Model.setText("Carneiro 4")
                    self.ui.lineEditTubIn.setText("1.1/4")
                    self.ui.lineEditTubOut.setText("1/2")
                elif vazao < 120:
                    print("Carneiro 5")
                    self.ui.lineEdit_FlowMax.setText("216")
                    self.ui.lineEdit_FlowMin.setText("540")
                    self.ui.lineEdit_Model.setText("Carneiro 5")
                    self.ui.lineEditTubIn.setText("2")
                    self.ui.lineEditTubOut.setText("3/4")
                else:
                    print("Carneiro 6")
                    self.ui.lineEdit_FlowMax.setText("1440")
                    self.ui.lineEdit_FlowMin.setText("576")
                    self.ui.lineEdit_Model.setText("Carneiro 6")
                    self.ui.lineEditTubIn.setText("3")
                    self.ui.lineEditTubOut.setText("1.25")
            except ValueError:
                print("Valor de vazão inválido. Certifique-se de inserir um número válido.")
            # Extract and convert values from UI elements
            selected_material1 = self.ui.comboBox_Rugosidade_In.currentText()
            rugosities = self.material_to_rugosity.get(selected_material1, "Rugosidade não especificada")
            # Exemplo de uso da função
            Q1 = float(self.ui.lineEditflow.text()) / 3600000  # Vazão (m³/s)
            D1 = float(self.ui.lineEditTubIn.text()) * 0.0254
            print(D1)
            L1 = float(self.ui.lineEditDistanciaFR.text())
            rugosidade = float(rugosities)  # Rugosidade da tubulação (m)
            print(rugosities)
            # Extract and convert values from UI elements
            selected_material2 = self.ui.comboBox_Rugosidade_Out.currentText()
            rugosities2 = self.material_to_rugosity.get(selected_material2, "Rugosidade não especificada")

            # Exemplo de uso da função
            Q2 = float(self.ui.lineEdit_FlowMax.text()) / 3600000  # Vazão (m³/s)
            D2 = float(self.ui.lineEditTubOut.text()) * 0.0254
            print(D2)
            L2 = float(self.ui.lineEditDistanciaFB.text())
            rugosidade2 = float(rugosities2)  # Rugosidade da tubulação (m)
            print(rugosities2)
            perda_total = perda_de_carga_Darcy_Weisbach(Q1, D1, L1, rugosidade)
            print(str(perda_total))
            # Display the result
            self.ui.lineEdit_LossIn.setText(f"{str(perda_total)[:8]}")
            perda_total2 = perda_de_carga_Darcy_Weisbach(Q2, D2, L2, rugosidade2)
            print(str(perda_total2))
            # Display the result
            self.ui.lineEdit_LossOut.setText(f"{str(perda_total2)[:8]}")
        except ValueError as e:
            print(f"Error: {e}")
            print("Invalid input values.")
        except Exception as e:
            print(f"Error: {e}")
            print("An unexpected error occurred.")

    def handleButtonClickCalculo(self):
        try:
            # Extract and convert values from UI elements
            lath1 = float(self.latfon)
            lonh1 = float(self.lngfon)
            alth1 = float(self.elevationfonte)
            lath2 = float(self.latreser)
            lonh2 = float(self.lngreser)
            alth2 = float(self.elevationreservatorio)
            # Calculate the distance with height difference using the haversine_with_height function
            distance_with_height1 = haversine_with_height(lath1, lonh1, alth1, lath2, lonh2, alth2)
            # Display the result
            self.ui.lineEditAlturaDeltaFR.setText(str(alth1 - alth2)[:5])
            self.ui.lineEditDistanciaFR.setText(str(distance_with_height1)[:5])
            lath2 = float(self.latpump)
            lonh2 = float(self.lngpump)
            alth2 = float(self.elevationpump)
            # Calculate the distance with height difference using the haversine_with_height function
            distance_with_height2 = haversine_with_height(lath1, lonh1, alth1, lath2, lonh2, alth2)
            self.ui.lineEditAlturaDeltaFB.setText(str(alth1 - alth2)[:5])
            self.ui.lineEditDistanciaFB.setText(str(distance_with_height2)[:5])
            lath1 = float(self.latreser)
            lonh1 = float(self.lngreser)
            alth1 = float(self.elevationreservatorio)
            distance_pump_reservoir = haversine_with_height(lath1, lonh1, alth1, lath2, lonh2, alth2)
            height_pump_reservoir = alth1 - alth2
            print(distance_pump_reservoir)
            print(height_pump_reservoir)
            if self.elevationfonte > self.elevationreservatorio:
                print("Você não precisa de uma bomba, a gravidade está seu favor")
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Aviso")
                msg_box.setText(
                    "Você não precisa de uma bomba, a gravidade está a seu favor.")
                msg_box.exec_()
            else:
                print("Reservatorio está acima da fonte, a bomba é necessária")
            if height_pump_reservoir > 40:
                print("Exibindo popup: A diferença das alturas é maior que 40 metros.")
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Aviso")
                msg_box.setText(
                    "A diferença de Altura entre a bomba e seu reservatório é maior que 40 metros, você excedeu os limites do fabricante.")
                msg_box.exec_()
            else:
                print("A diferença das alturas não é maior que 40.")
            if distance_pump_reservoir > 400:
                print("Exibindo popup: A diferença das distâncias é maior que 400 metros.")
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Aviso")
                msg_box.setText(
                    "A diferença das distâncias é maior que 400 metros, você excedeu os limites do fabricante.")
                msg_box.exec_()
            else:
                print("A diferença das distâncias não é maior que 400.")

        except ValueError as e:
            print(f"Error: {e}")
            print("Invalid input values. Please check the latitude, longitude, and elevation values.")
        except Exception as e:
            print(f"Error: {e}")
            print("An unexpected error occurred.")

    def handleButtonClickCalculoFluxo(self):
        try:
            # Extract and convert values from UI elements
            lath1 = float(self.latfon)
            lonh1 = float(self.lngfon)
            area = float(self.ui.lineEditArea.text())
            self.fluxomapa = (float((extract_value(lath1, lonh1, area))) * 1000) / 60
            # Display the result
            self.ui.lineEditflow.setText(f"{str(self.fluxomapa)[:8]}")
            print(area)
        except ValueError as e:
            print(f"Error: {e}")
            print("Invalid input values. Please check the latitude, longitude, and area values.")
        except Exception as e:
            print(f"Error: {e}")
            print("An unexpected error occurred.")

    def handleButtonClickres(self):
        if self.lat is not None and self.lng is not None:
            self.ui.lineEditLAR.setText(str(self.lat)[:12])
            self.ui.lineEditLOR.setText(str(self.lng)[:12])
            self.latreser = (str(self.lat)[:10])
            self.lngreser = (str(self.lng)[:10])
            print(self.latreser)
            print(self.lngreser)
            params = {
                'locations': f"{self.latreser},{self.lngreser}",
                'key': "INSERT YOUR KEY"
            }
            response = requests.get(BASE_URL, params=params)
            data = response.json()
            if data.get('results'):
                self.elevationreservatorio = data['results'][0]['elevation']
                self.ui.lineEditAlturaReservatorio.setText(str(self.elevationreservatorio)[:5])
                print(self.elevationreservatorio)
            else:
                print("Obtenção de dados indisponível")
        else:
            print("Coordinates not available")

    def handleButtonClickfon(self):
        if self.lat is not None and self.lng is not None:
            self.ui.lineEditLAF.setText(str(self.lat)[:12])
            self.ui.lineEditLOF.setText(str(self.lng)[:12])
            self.latfon = (str(self.lat)[:10])
            self.lngfon = (str(self.lng)[:10])
            print(self.lngfon)
            print(self.latfon)
            params = {
                'locations': f"{self.latfon},{self.lngfon}",
                'key': "AIzaSyCHfKgESVCt6zp5IdmfOYHxs1ljjLUYLsA"
            }
            response = requests.get(BASE_URL, params=params)
            data = response.json()
            if data.get('results'):
                self.elevationfonte = data['results'][0]['elevation']
                self.ui.lineEditAlturaFonte.setText(str(self.elevationfonte)[:5])
                print(self.elevationfonte)
            else:
                print("Obtenção de dados indisponível")
        else:
            print("Coordinates not available")

    def handleButtonClickpump(self):
        if self.lat is not None and self.lng is not None:
            self.ui.lineEditLAB.setText(str(self.lat)[:12])
            self.ui.lineEditLOB.setText(str(self.lng)[:12])
            self.latpump = (str(self.lat)[:10])
            self.lngpump = (str(self.lng)[:10])
            print(self.lngpump)
            print(self.latpump)
            params = {
                'locations': f"{self.latpump},{self.lngpump}",
                'key': "AIzaSyCHfKgESVCt6zp5IdmfOYHxs1ljjLUYLsA"
            }
            response = requests.get(BASE_URL, params=params)
            data = response.json()
            if data.get('results'):
                self.elevationpump = data['results'][0]['elevation']
                self.ui.lineEditAlturaBomba.setText(str(self.elevationpump)[:5])
                print(self.elevationpump)
            else:
                print("Obtenção de dados indisponível")
        else:
            print("Coordinates not available")

    def handleConsoleMessage(self, msg):
        try:
            data = json.loads(msg)
            self.lat = data['coordinates']['lat']
            self.lng = data['coordinates']['lng']
            coords = f"latitude: {self.lat} longitude: {self.lng}"
            print("Selected coordinates:", coords)
        except Exception as e:
            print("Exception:", e)
            traceback.print_exc()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Tela()
    w.show()
    sys.exit(app.exec_())
