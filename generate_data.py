import json
import random

# Domains: travel, work, healthcare, education, tech, finance, legal/admin, everyday chat, news, arts

# Travel
travel_en = [
    "I would like to book a flight to {city}.",
    "Where is the nearest {place}?",
    "Can I have a map of the city?",
    "Is breakfast included in the room price?",
    "The train to {city} leaves at {time}.",
    "We need to check out before {time}.",
    "How much does a taxi to the airport cost?",
    "Could you recommend a good local restaurant?",
    "I lost my passport, where is the embassy?",
    "Which platform does the train to {city} depart from?",
    "Are there any guided tours available in {lang}?",
    "I'd like to rent a car for {num} days.",
    "Is there a direct bus to the {place}?",
    "Can I pay with a credit card here?",
    "The flight was delayed by {num} hours.",
    "The hotel is located in the heart of the city.",
    "Do you have any vacancies for tonight?",
    "I need a window seat if possible.",
    "The baggage allowance is {num} kilograms.",
    "Where can I exchange some money?",
]
travel_es = [
    "Me gustaría reservar un vuelo a {city}.",
    "¿Dónde está el {place} más cercano?",
    "¿Podría darme un mapa de la ciudad?",
    "¿El desayuno está incluido en el precio de la habitación?",
    "El tren a {city} sale a las {time}.",
    "Tenemos que dejar la habitación antes de las {time}.",
    "¿Cuánto cuesta un taxi al aeropuerto?",
    "¿Podría recomendarme un buen restaurante local?",
    "He perdido mi pasaporte, ¿dónde está la embajada?",
    "¿De qué andén sale el tren hacia {city}?",
    "¿Hay visitas guiadas disponibles en {lang}?",
    "Me gustaría alquilar un coche por {num} días.",
    "¿Hay un autobús directo al {place}?",
    "¿Puedo pagar con tarjeta de crédito aquí?",
    "El vuelo se retrasó {num} horas.",
    "El hotel está situado en el corazón de la ciudad.",
    "¿Tienen habitaciones libres para esta noche?",
    "Necesito un asiento de ventana si es posible.",
    "El límite de equipaje es de {num} kilogramos.",
    "¿Dónde puedo cambiar algo de dinero?",
]

# Work
work_en = [
    "The meeting has been rescheduled for {time}.",
    "Could you please send me the {doc} by the end of the day?",
    "We need to discuss the project timeline during our next call.",
    "The deadline for the report is {day} morning.",
    "I am currently out of the office and will return on {day}.",
    "Please find the attached invoice for the services provided.",
    "The company is expanding its operations into {country}.",
    "We are looking for a candidate with at least {num} years of experience.",
    "The performance review will take place next {day}.",
    "I need to coordinate with the {dept} department on this matter.",
    "The new software update will be rolled out next week.",
    "Can we jump on a quick call to sync on the current tasks?",
    "The presentation for the board is almost ready.",
    "We need to reduce our overhead costs by {num} percent.",
    "The recruitment process will start next month.",
    "I'll be working from home on {day}.",
    "The team reached its quarterly goals ahead of schedule.",
    "Could you review the proposal and give me your feedback?",
    "The office will be closed for the public holiday on {day}.",
    "We are implementing a new hybrid work policy.",
]
work_es = [
    "La reunión se ha reprogramado para las {time}.",
    "¿Podría enviarme el {doc} antes de que termine el día?",
    "Tenemos que discutir el cronograma del proyecto en nuestra próxima llamada.",
    "La fecha límite para el informe es el {day} por la mañana.",
    "Actualmente estoy fuera de la oficina y volveré el {day}.",
    "Adjunto encontrará la factura por los servicios prestados.",
    "La empresa está expandiendo sus operaciones a {country}.",
    "Buscamos un candidato con al menos {num} años de experiencia.",
    "La evaluación de desempeño tendrá lugar el próximo {day}.",
    "Necesito coordinar con el departamento de {dept} sobre este asunto.",
    "La nueva actualización de software se lanzará la próxima semana.",
    "¿Podemos hacer una llamada rápida para sincronizar las tareas actuales?",
    "La presentación para la junta está casi lista.",
    "Necesito reducir nuestros costos fijos en un {num} por ciento.",
    "El proceso de contratación comenzará el próximo mes.",
    "Estaré trabajando desde casa el {day}.",
    "El equipo alcanzó sus objetivos trimestrales antes de lo previsto.",
    "¿Podría revisar la propuesta y darme sus comentarios?",
    "La oficina estará cerrada por el día festivo el {day}.",
    "Estamos implementando una nueva política de trabajo híbrido.",
]

# Healthcare
health_en = [
    "You should take this medication {num} times a day.",
    "The patient is recovering well after the surgery.",
    "I need to make an appointment with a {specialist}.",
    "Where is the nearest pharmacy that is open {num} hours?",
    "Do you have any allergies to certain drugs?",
    "The results of your blood test will be ready in {num} days.",
    "Please fill out this medical history form before seeing the doctor.",
    "The doctor recommended a diet low in {item}.",
    "It is important to maintain a healthy lifestyle to prevent {disease}.",
    "The hospital has state-of-the-art equipment for diagnosis.",
    "I have been feeling {symptom} for the past few days.",
    "The vaccination clinic is open from {time} to {time}.",
    "You need a prescription to buy this medicine.",
    "The surgery was successful and the patient is stable.",
    "Drink plenty of water and get enough rest.",
    "The nurse will take your blood pressure now.",
    "Are you experiencing any side effects from the treatment?",
    "The rehabilitation process can take several months.",
    "Early detection of {disease} is crucial for recovery.",
    "The clinic offers free consultations for senior citizens.",
]
health_es = [
    "Debe tomar este medicamento {num} veces al día.",
    "El paciente se está recuperando bien después de la cirugía.",
    "Necesito pedir una cita con un {specialist}.",
    "¿Dónde está la farmacia más cercana que abra {num} horas?",
    "¿Tiene alguna alergia a ciertos medicamentos?",
    "Los resultados de su análisis de sangre estarán listos en {num} días.",
    "Por favor, complete este formulario de historial médico antes de ver al doctor.",
    "El médico recomendó una dieta baja en {item}.",
    "Es importante mantener un estilo de vida saludable para prevenir {disease}.",
    "El hospital cuenta con equipos de última generación para el diagnóstico.",
    "Me he sentido {symptom} durante los últimos días.",
    "La clínica de vacunación está abierta de {time} a {time}.",
    "Necesita una receta para comprar este medicamento.",
    "La cirugía fue exitosa y el paciente se encuentra estable.",
    "Beba mucha agua y descanse lo suficiente.",
    "La enfermera le tomará la presión arterial ahora.",
    "¿Está experimentando algún efecto secundario por el tratamiento?",
    "El proceso de rehabilitación puede durar varios meses.",
    "La detección temprana de {disease} es crucial para la recuperación.",
    "La clínica ofrece consultas gratuitas para personas mayores.",
]

# Education
edu_en = [
    "The university offers a wide range of undergraduate courses.",
    "I need to study for my {subject} exam on {day}.",
    "The deadline for the scholarship application is {date}.",
    "The professor published a new research paper on {topic}.",
    "Students are required to attend at least {num} percent of the lectures.",
    "The library has a vast collection of academic journals.",
    "She graduated with honors in {subject} from {university}.",
    "The school is organizing a field trip to the museum next {day}.",
    "I'm considering doing a master's degree in {topic}.",
    "The tuition fees for international students have increased.",
    "Online learning has become more popular in recent years.",
    "The textbook provides a comprehensive overview of the subject.",
    "He received a full scholarship to study abroad.",
    "The campus has modern facilities for sports and recreation.",
    "I need to return these books to the library by {time}.",
    "The graduation ceremony will be held in the main hall.",
    "We have a group project due next week for the {subject} class.",
    "The teacher explained the complex concepts very clearly.",
    "Vocational training programs are gaining more attention.",
    "The school district is investing in new technology for classrooms.",
]
edu_es = [
    "La universidad ofrece una amplia gama de cursos de grado.",
    "Necesito estudiar para mi examen de {subject} el {day}.",
    "La fecha límite para la solicitud de beca es el {date}.",
    "El profesor publicó un nuevo artículo de investigación sobre {topic}.",
    "Se requiere que los estudiantes asistan al menos al {num} por ciento de las clases.",
    "La biblioteca tiene una vasta colección de revistas académicas.",
    "Ella se graduó con honores en {subject} por la {university}.",
    "La escuela está organizando una excursión al museo el próximo {day}.",
    "Estoy considerando hacer una maestría en {topic}.",
    "Las tasas de matrícula para estudiantes internacionales han aumentado.",
    "El aprendizaje en línea se ha vuelto más popular en los últimos años.",
    "El libro de texto ofrece una visión integral de la materia.",
    "Recibió una beca completa para estudiar en el extranjero.",
    "El campus cuenta con instalaciones modernas para deportes y recreación.",
    "Tengo que devolver estos libros a la biblioteca antes de las {time}.",
    "La ceremonia de graduación se llevará a cabo en el salón principal.",
    "Tenemos un proyecto grupal para la clase de {subject} la próxima semana.",
    "El profesor explicó los conceptos complejos con mucha claridad.",
    "Los programas de formación profesional están ganando más atención.",
    "El distrito escolar está invirtiendo en nueva tecnología para las aulas.",
]

# Tech
tech_en = [
    "The new smartphone features a high-resolution camera and {num}G connectivity.",
    "Artificial intelligence is transforming many industries.",
    "Make sure to back up your data to the cloud regularly.",
    "The software update fixes several security vulnerabilities.",
    "The company is developing a new app for {platform}.",
    "Broadband speeds have improved significantly in this area.",
    "The data center uses renewable energy to power its servers.",
    "Blockchain technology can provide a more secure way to handle transactions.",
    "The user interface of the website is very intuitive.",
    "I need to reset my password for the {service} account.",
    "The startup raised {num} million dollars in its latest funding round.",
    "Cybersecurity is a top priority for most large corporations.",
    "The gadget is compatible with both iOS and Android.",
    "We are moving our infrastructure to the cloud next month.",
    "The developer is working on a new feature for the {app} app.",
    "Quantum computing could solve problems that are currently impossible for classical computers.",
    "The battery life of the laptop is approximately {num} hours.",
    "I bought a new smart home device that works with {voice_assistant}.",
    "The open-source community is very active in this project.",
    "The gaming console supports 4K resolution at {num} frames per second.",
]
tech_es = [
    "El nuevo smartphone cuenta con una cámara de alta resolución y conectividad {num}G.",
    "La inteligencia artificial está transformando muchas industrias.",
    "Asegúrese de hacer copias de seguridad de sus datos en la nube regularmente.",
    "La actualización de software corrige varias vulnerabilidades de seguridad.",
    "La empresa está desarrollando una nueva aplicación para {platform}.",
    "Las velocidades de banda ancha han mejorado significativamente en esta zona.",
    "El centro de datos utiliza energía renovable para alimentar sus servidores.",
    "La tecnología blockchain puede proporcionar una forma más segura de gestionar transacciones.",
    "La interfaz de usuario del sitio web es muy intuitiva.",
    "Necesito restablecer mi contraseña para la cuenta de {service}.",
    "La startup recaudó {num} millones de dólares en su última ronda de financiación.",
    "La ciberseguridad es una prioridad absoluta para la mayoría de las grandes corporaciones.",
    "El dispositivo es compatible tanto con iOS como con Android.",
    "Vamos a trasladar nuestra infraestructura a la nube el próximo mes.",
    "El desarrollador está trabajando en una nueva función para la aplicación {app}.",
    "La computación cuántica podría resolver problemas que actualmente son imposibles para los ordenadores clásicos.",
    "La duración de la batería del portátil es de aproximadamente {num} horas.",
    "Compré un nuevo dispositivo doméstico inteligente que funciona con {voice_assistant}.",
    "La comunidad de código abierto es muy activa en este proyecto.",
    "La consola de juegos admite resolución 4K a {num} fotogramas por segundo.",
]

# Finance
fin_en = [
    "The stock market experienced a significant drop yesterday.",
    "I'm looking for a low-interest loan to start a small business.",
    "The central bank decided to keep the interest rates unchanged.",
    "The company's quarterly earnings exceeded analyst expectations.",
    "Diversifying your portfolio can help reduce investment risk.",
    "The inflation rate has increased by {num} percent this year.",
    "I need to open a savings account with a higher interest rate.",
    "The exchange rate between the dollar and the euro is currently {rate}.",
    "Real estate is often considered a safe long-term investment.",
    "The government is implementing new tax incentives for small businesses.",
    "The global economy is showing signs of recovery.",
    "I'm considering investing in index funds for my retirement.",
    "The merger between the two banks was approved by regulators.",
    "Cryptocurrencies are known for their high volatility.",
    "The national debt has reached an all-time high.",
    "I need to talk to a financial advisor about my pension plan.",
    "The trade deficit has narrowed in the last quarter.",
    "Commodity prices like oil and gold have been fluctuating recently.",
    "The budget for the next fiscal year will be presented tomorrow.",
    "Venture capital firms are investing heavily in biotech startups.",
]
fin_es = [
    "La bolsa de valores experimentó una caída significativa ayer.",
    "Busco un préstamo a bajo interés para iniciar una pequeña empresa.",
    "El banco central decidió mantener los tipos de interés sin cambios.",
    "Las ganancias trimestrales de la empresa superaron las expectativas de los analistas.",
    "Diversificar su cartera puede ayudar a reducir el riesgo de inversión.",
    "La tasa de inflación ha aumentado un {num} por ciento este año.",
    "Necesito abrir una cuenta de ahorros con un tipo de interés más alto.",
    "El tipo de cambio entre el dólar y el euro es actualmente de {rate}.",
    "Los bienes raíces a menudo se consideran una inversión segura a largo plazo.",
    "El gobierno está implementando nuevos incentivos fiscales para las pequeñas empresas.",
    "La economía global está mostrando signos de recuperación.",
    "Estoy considerando invertir en fondos indexados para mi jubilación.",
    "La fusión entre los dos bancos fue aprobada por los reguladores.",
    "Las criptomonedas son conocidas por su alta volatilidad.",
    "La deuda nacional ha alcanzado un máximo histórico.",
    "Necesito hablar con un asesor financiero sobre mi plan de pensiones.",
    "El déficit comercial se ha reducido en el último trimestre.",
    "Los precios de las materias primas como el petróleo y el oro han estado fluctuando recientemente.",
    "El presupuesto para el próximo año fiscal se presentará mañana.",
    "Las empresas de capital riesgo están invirtiendo fuertemente en startups biotecnológicas.",
]

# Legal/Admin
legal_en = [
    "The contract must be signed by both parties to be valid.",
    "I need to apply for a building permit for the renovation.",
    "The witness provided a detailed account of the incident in court.",
    "The new law aims to protect the rights of consumers.",
    "The legal proceedings are expected to last several months.",
    "You should consult with a lawyer before signing any legal documents.",
    "The defendant was found not guilty of the charges.",
    "The government is proposing new regulations for environmental protection.",
    "I need to renew my driver's license at the local DMV.",
    "The terms and conditions of the agreement are clearly stated.",
    "The copyright for this work belongs to the author.",
    "The court issued an injunction against the company.",
    "I'm seeking legal advice regarding a property dispute.",
    "The administrative process can be quite slow at times.",
    "The patent for the new invention was granted last month.",
    "The notary will verify the signatures on the document.",
    "The judge dismissed the case due to lack of evidence.",
    "Mediation can be a faster way to resolve disputes.",
    "The policy changes will take effect from the first of next month.",
    "I need to fill out several forms to apply for a visa.",
]
legal_es = [
    "El contrato debe ser firmado por ambas partes para ser válido.",
    "Necesito solicitar un permiso de obra para la renovación.",
    "El testigo ofreció un relato detallado del incidente ante el tribunal.",
    "La nueva ley tiene como objetivo proteger los derechos de los consumidores.",
    "Se espera que el proceso legal dure varios meses.",
    "Debe consultar con un abogado antes de firmar cualquier documento legal.",
    "El acusado fue declarado no culpable de los cargos.",
    "El gobierno está proponiendo nuevas regulaciones para la protección del medio ambiente.",
    "Necesito renovar mi carné de conducir en la oficina de tráfico local.",
    "Los términos y condiciones del acuerdo están claramente establecidos.",
    "Los derechos de autor de esta obra pertenecen al autor.",
    "El tribunal dictó una orden judicial contra la empresa.",
    "Busco asesoramiento legal en relación con una disputa de propiedad.",
    "El proceso administrativo puede ser bastante lento a veces.",
    "La patente del nuevo invento fue concedida el mes pasado.",
    "El notario verificará las firmas en el documento.",
    "El juez desestimó el caso por falta de pruebas.",
    "La mediación puede ser una forma más rápida de resolver disputas.",
    "Los cambios de política entrarán en vigor a partir del primero del próximo mes.",
    "Tengo que rellenar varios formularios para solicitar el visado.",
]

# Everyday Chat
chat_en = [
    "What are you planning to do this weekend?",
    "I'm so tired today, I didn't sleep well last night.",
    "Would you like to grab a coffee sometime this week?",
    "It's been a long time since we last met.",
    "Did you see the latest episode of that show?",
    "I'm thinking of going for a run in the park.",
    "That sounds like a great idea!",
    "I'm really looking forward to the holiday.",
    "How is your family doing?",
    "I just bought a new book and I can't wait to start reading it.",
    "The weather is so nice today, let's go outside.",
    "I'm sorry I'm late, the traffic was terrible.",
    "What's your favorite type of food?",
    "I had a really busy day at work today.",
    "Do you have any plans for tonight?",
    "It was great seeing you again.",
    "I'm feeling much better now, thanks for asking.",
    "Can you believe how fast this year is going?",
    "I'm going to cook something special for dinner tonight.",
    "Let me know if you need any help with that.",
]
chat_es = [
    "¿Qué tienes pensado hacer este fin de semana?",
    "Estoy tan cansado hoy, no dormí bien anoche.",
    "¿Te apetece tomar un café en algún momento de esta semana?",
    "Ha pasado mucho tiempo desde la última vez que nos vimos.",
    "¿Viste el último episodio de esa serie?",
    "Estoy pensando en ir a correr al parque.",
    "¡Eso suena como una gran idea!",
    "Tengo muchas ganas de que lleguen las vacaciones.",
    "¿Cómo está tu familia?",
    "Acabo de comprar un libro nuevo y no puedo esperar a empezar a leerlo.",
    "Hace tan buen tiempo hoy, salgamos fuera.",
    "Siento llegar tarde, el tráfico era terrible.",
    "¿Cuál es tu tipo de comida favorita?",
    "Hoy he tenido un día muy ajetreado en el trabajo.",
    "¿Tienes algún plan para esta noche?",
    "Fue genial volver a verte.",
    "Me siento mucho mejor ahora, gracias por preguntar.",
    "¿Puedes creer lo rápido que está pasando este año?",
    "Voy a cocinar algo especial para cenar esta noche.",
    "Avísame si necesitas ayuda con eso.",
]

# News
news_en = [
    "The prime minister is scheduled to give a speech at {time}.",
    "Heavy rain caused flooding in several parts of the country.",
    "The scientists discovered a new species of plants in the Amazon.",
    "The summit will focus on climate change and global security.",
    "Local residents are protesting against the construction of a new highway.",
    "The national team won the championship after a thrilling match.",
    "The unemployment rate reached its lowest level in a decade.",
    "A major earthquake struck the region early this morning.",
    "The company announced it will create {num} new jobs in the city.",
    "The international community condemned the recent acts of violence.",
    "Spacecraft successfully landed on the surface of {planet}.",
    "New research suggests that the climate is changing faster than expected.",
    "The museum is hosting a special exhibition on ancient civilizations.",
    "Traffic was disrupted on the main bridge due to an accident.",
    "The city is preparing for the annual festival next month.",
    "The report highlights the growing gap between rich and poor.",
    "Police are investigating a series of robberies in the downtown area.",
    "The election results will be announced late tonight.",
    "A new bridge will be built to connect the two islands.",
    "The healthcare system is facing a shortage of nurses and doctors.",
]
news_es = [
    "Está previsto que el primer ministro dé un discurso a las {time}.",
    "Las fuertes lluvias causaron inundaciones en varias partes del país.",
    "Los científicos descubrieron una nueva especie de plantas en el Amazonas.",
    "La cumbre se centrará en el cambio climático y la seguridad global.",
    "Los residentes locales protestan contra la construcción de una nueva autopista.",
    "La selección nacional ganó el campeonato tras un partido emocionante.",
    "La tasa de desempleo alcanzó su nivel más bajo en una década.",
    "Un gran terremoto sacudió la región a primera hora de esta mañana.",
    "La empresa anunció que creará {num} nuevos puestos de trabajo en la ciudad.",
    "La comunidad internacional condenó los recientes actos de violencia.",
    "La nave espacial aterrizó con éxito en la superficie de {planet}.",
    "Nuevas investigaciones sugieren que el clima está cambiando más rápido de lo esperado.",
    "El museo acoge una exposición especial sobre civilizaciones antiguas.",
    "El tráfico se vio interrumpido en el puente principal debido a un accidente.",
    "La ciudad se prepara para el festival anual del próximo mes.",
    "El informe destaca la creciente brecha entre ricos y pobres.",
    "La policía investiga una serie de robos en la zona centro.",
    "Los resultados de las elecciones se anunciarán a última hora de esta noche.",
    "Se construirá un nuevo puente para conectar las dos islas.",
    "El sistema sanitario se enfrenta a una escasez de enfermeras y médicos.",
]

# Arts/Literature
arts_en = [
    "The novel tells the story of a young artist in {city}.",
    "The art gallery is exhibiting works by local painters.",
    "The theater production received rave reviews from critics.",
    "The museum's collection includes several masterpieces from the {period}.",
    "He is a well-known poet who has published several volumes of poetry.",
    "The symphony was composed in the early {num}th century.",
    "The architecture of the building is a mix of modern and classical styles.",
    "The film won the prestigious award for best director.",
    "I enjoy reading classical literature in my spare time.",
    "The concert will feature a performance by a world-renowned pianist.",
    "The sculpture was carved from a single block of marble.",
    "The festival celebrates the cultural heritage of the region.",
    "The play explores themes of love, loss, and redemption.",
    "The writer's style is characterized by its lyrical prose.",
    "The mural depicts scenes from the city's history.",
    "The ballet company is performing a new production of {ballet}.",
    "The opera house is known for its incredible acoustics.",
    "The photographer captured the beauty of the landscape at sunset.",
    "The exhibition showcases the evolution of contemporary art.",
    "The library has a rare collection of ancient manuscripts.",
]
arts_es = [
    "La novela cuenta la historia de un joven artista en {city}.",
    "La galería de arte expone obras de pintores locales.",
    "La producción teatral recibió críticas excelentes de los expertos.",
    "La colección del museo incluye varias obras maestras del {period}.",
    "Es un poeta muy conocido que ha publicado varios volúmenes de poesía.",
    "La sinfonía fue compuesta a principios del siglo {num}.",
    "La arquitectura del edificio es una mezcla de estilos moderno y clásico.",
    "La película ganó el prestigioso premio al mejor director.",
    "Disfruto leyendo literatura clásica en mi tiempo libre.",
    "El concierto contará con la actuación de un pianista de fama mundial.",
    "La escultura fue tallada en un solo bloque de mármol.",
    "El festival celebra el patrimonio cultural de la región.",
    "La obra explora temas como el amor, la pérdida y la redención.",
    "El estilo del escritor se caracteriza por su prosa lírica.",
    "El mural representa escenas de la historia de la ciudad.",
    "La compañía de ballet representa una nueva producción de {ballet}.",
    "El teatro de la ópera es conocido por su increíble acústica.",
    "El fotógrafo captó la belleza del paisaje al atardecer.",
    "La exposición muestra la evolución del arte contemporáneo.",
    "La biblioteca posee una rara colección de manuscritos antiguos.",
]

cities = ["London", "Paris", "New York", "Madrid", "Barcelona", "Tokyo", "Rome", "Berlin", "Sydney", "Mexico City", "Buenos Aires", "Bogotá"]
cities_es = ["Londres", "París", "Nueva York", "Madrid", "Barcelona", "Tokio", "Roma", "Berlín", "Sídney", "Ciudad de México", "Buenos Aires", "Bogotá"]
places = ["bank", "supermarket", "pharmacy", "train station", "bus stop", "hospital", "museum", "library", "park", "square"]
places_es = ["banco", "supermercado", "farmacia", "estación de tren", "parada de autobús", "hospital", "museo", "biblioteca", "parque", "plaza"]
langs = ["English", "Spanish", "French", "German", "Italian", "Japanese", "Chinese"]
langs_es = ["inglés", "español", "francés", "alemán", "italiano", "japonés", "chino"]
times = ["9:00 AM", "10:30 AM", "12:00 PM", "2:15 PM", "4:30 PM", "6:00 PM", "8:45 PM"]
times_es = ["las 9:00", "las 10:30", "las 12:00", "las 14:15", "las 16:30", "las 18:00", "las 20:45"]
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
days_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
countries = ["Spain", "Mexico", "the United States", "Canada", "France", "Germany", "Japan", "Brazil", "Argentina", "Chile"]
countries_es = ["España", "México", "Estados Unidos", "Canadá", "Francia", "Alemania", "Japón", "Brasil", "Argentina", "Chile"]
depts = ["human resources", "finance", "marketing", "sales", "IT", "legal", "operations"]
depts_es = ["recursos humanos", "finanzas", "marketing", "ventas", "informática", "legal", "operaciones"]
specialists = ["cardiologist", "dentist", "pediatrician", "dermatologist", "neurologist", "orthopedist"]
specialists_es = ["cardiólogo", "dentista", "pediatra", "dermatólogo", "neurólogo", "traumatólogo"]
subjects = ["history", "mathematics", "biology", "physics", "chemistry", "literature", "economics"]
subjects_es = ["historia", "matemáticas", "biología", "física", "química", "literatura", "economía"]
diseases = ["diabetes", "heart disease", "cancer", "hypertension", "asthma"]
diseases_es = ["diabetes", "enfermedades cardíacas", "cáncer", "hipertensión", "asma"]
symptoms = ["a headache", "a fever", "a sore throat", "a cough", "fatigue", "dizziness"]
symptoms_es = ["dolor de cabeza", "fiebre", "dolor de garganta", "tos", "fatiga", "mareos"]
platforms = ["iOS", "Android", "Web", "Windows", "macOS", "Linux"]
apps = ["productivity", "social media", "fitness", "banking", "messaging", "e-commerce"]
voice_assistants = ["Alexa", "Google Assistant", "Siri"]
periods = ["Renaissance", "Baroque", "Romanticism", "Modernism", "Impressionism"]
ballets = ["The Nutcracker", "Swan Lake", "Giselle", "Romeo and Juliet"]
planets = ["Mars", "Venus", "Jupiter", "the Moon", "Saturn"]

def generate_row(src_lang, tgt_lang, domain_en, domain_es):
    idx = random.randint(0, len(domain_en) - 1)
    en_tpl = domain_en[idx]
    es_tpl = domain_es[idx]
    
    # Fill placeholders
    city_idx = random.randint(0, len(cities) - 1)
    place_idx = random.randint(0, len(places) - 1)
    lang_idx = random.randint(0, len(langs) - 1)
    time_idx = random.randint(0, len(times) - 1)
    day_idx = random.randint(0, len(days) - 1)
    country_idx = random.randint(0, len(countries) - 1)
    dept_idx = random.randint(0, len(depts) - 1)
    specialist_idx = random.randint(0, len(specialists) - 1)
    subject_idx = random.randint(0, len(subjects) - 1)
    disease_idx = random.randint(0, len(diseases) - 1)
    symptom_idx = random.randint(0, len(symptoms) - 1)
    platform_idx = random.randint(0, len(platforms) - 1)
    app_idx = random.randint(0, len(apps) - 1)
    va_idx = random.randint(0, len(voice_assistants) - 1)
    period_idx = random.randint(0, len(periods) - 1)
    ballet_idx = random.randint(0, len(ballets) - 1)
    planet_idx = random.randint(0, len(planets) - 1)
    
    num = random.randint(1, 100)
    rate = f"{random.uniform(0.5, 1.5):.2f}"
    
    vals_en = {
        "city": cities[city_idx], "place": places[place_idx], "lang": langs[lang_idx], "time": times[time_idx],
        "day": days[day_idx], "country": countries[country_idx], "dept": depts[dept_idx], "doc": "document",
        "specialist": specialists[specialist_idx], "num": num, "item": "sugar", "disease": diseases[disease_idx],
        "symptom": symptoms[symptom_idx], "subject": subjects[subject_idx], "date": f"June {num}",
        "topic": "sustainable development", "university": "the University of Madrid", "platform": platforms[platform_idx],
        "service": "email", "app": apps[app_idx], "voice_assistant": voice_assistants[va_idx], "rate": rate,
        "period": periods[period_idx], "ballet": ballets[ballet_idx], "planet": planets[planet_idx]
    }
    vals_es = {
        "city": cities_es[city_idx], "place": places_es[place_idx], "lang": langs_es[lang_idx], "time": times_es[time_idx],
        "day": days_es[day_idx], "country": countries_es[country_idx], "dept": depts_es[dept_idx], "doc": "documento",
        "specialist": specialists_es[specialist_idx], "num": num, "item": "azúcar", "disease": diseases_es[disease_idx],
        "symptom": symptoms_es[symptom_idx], "subject": subjects_es[subject_idx], "date": f"{num} de junio",
        "topic": "desarrollo sostenible", "university": "la Universidad de Madrid", "platform": platforms[platform_idx],
        "service": "correo electrónico", "app": apps[app_idx], "voice_assistant": voice_assistants[va_idx], "rate": rate,
        "period": periods[period_idx], "ballet": ballets[ballet_idx], "planet": planets[planet_idx]
    }
    
    try:
        source_text = en_tpl.format(**vals_en) if src_lang == "en" else es_tpl.format(**vals_es)
        pos_text = es_tpl.format(**vals_es) if tgt_lang == "es" else en_tpl.format(**vals_en)
    except KeyError as e:
        # Fallback if a template has an unexpected key
        return None
    
    # Generate negative: pick a random other template from the same domain
    neg_idx = idx
    while neg_idx == idx:
        neg_idx = random.randint(0, len(domain_en) - 1)
    neg_tpl_en = domain_en[neg_idx]
    neg_tpl_es = domain_es[neg_idx]
    
    try:
        neg_text = neg_tpl_es.format(**vals_es) if tgt_lang == "es" else neg_tpl_en.format(**vals_en)
    except KeyError:
        return None
    
    return {
        "src_lang": src_lang,
        "tgt_lang": tgt_lang,
        "pair": f"{src_lang}-{tgt_lang}",
        "source": source_text,
        "target_pos": pos_text,
        "target_neg": neg_text,
        "lang": tgt_lang,
        "query": source_text,
        "pos": pos_text,
        "neg": neg_text
    }

domains = [
    (travel_en, travel_es),
    (work_en, work_es),
    (health_en, health_es),
    (edu_en, edu_es),
    (tech_en, tech_es),
    (fin_en, fin_es),
    (legal_en, legal_es),
    (chat_en, chat_es),
    (news_en, news_es),
    (arts_en, arts_es)
]

new_rows = []
seen_sources = set()

# Load existing to avoid duplicates
with open("existing_rows.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        seen_sources.add(data["source"])

target_new = 9220
target_en_es = target_new // 2
target_es_en = target_new - target_en_es

en_es_count = 0
while en_es_count < target_en_es:
    dom_en, dom_es = random.choice(domains)
    row = generate_row("en", "es", dom_en, dom_es)
    if row and row["source"] not in seen_sources:
        new_rows.append(row)
        seen_sources.add(row["source"])
        en_es_count += 1
        if en_es_count % 500 == 0:
            print(f"Generated {en_es_count} en-es rows...")

es_en_count = 0
while es_en_count < target_es_en:
    dom_en, dom_es = random.choice(domains)
    row = generate_row("es", "en", dom_en, dom_es)
    if row and row["source"] not in seen_sources:
        new_rows.append(row)
        seen_sources.add(row["source"])
        es_en_count += 1
        if es_en_count % 500 == 0:
            print(f"Generated {es_en_count} es-en rows...")

# Mix them up
random.shuffle(new_rows)

# Read existing rows and fix them
fixed_existing = []
with open("existing_rows.jsonl", "r") as f:
    for line in f:
        data = json.loads(line)
        # Enforce pos == target_pos, neg == target_neg
        data["pos"] = data["target_pos"]
        data["neg"] = data["target_neg"]
        fixed_existing.append(data)

# Write all back
with open("projects/distillation/translation/training_data/translate_distill_pairs_en_es_2way.train.jsonl", "w") as f:
    for row in fixed_existing:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    for row in new_rows:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"Total rows: {len(fixed_existing) + len(new_rows)}")
