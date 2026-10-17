"""Generate Malay treatment PDFs for RAG testing."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib import colors
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "documents")
os.makedirs(OUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
body_style = ParagraphStyle(
    "MalayBody",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=11,
    leading=16,
    alignment=TA_JUSTIFY,
    spaceAfter=8,
)
heading_style = ParagraphStyle(
    "MalayHeading",
    parent=styles["Heading1"],
    fontSize=18,
    spaceAfter=12,
    spaceBefore=20,
    textColor=colors.HexColor("#0071e3"),
)
subheading_style = ParagraphStyle(
    "MalaySubHeading",
    parent=styles["Heading2"],
    fontSize=14,
    spaceAfter=8,
    spaceBefore=14,
    textColor=colors.HexColor("#1d1d1f"),
)


def build_pdf(filename, title, sections):
    """sections = [(heading, [paragraphs]), ...]"""
    path = os.path.join(OUT_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=25*mm, bottomMargin=25*mm)
    story = []
    story.append(Paragraph(title, heading_style))
    story.append(Spacer(1, 10*mm))

    for heading, paragraphs in sections:
        story.append(Paragraph(heading, subheading_style))
        for p in paragraphs:
            story.append(Paragraph(p, body_style))
        story.append(Spacer(1, 4*mm))

    doc.build(story)
    print(f"  Generated: {path}")
    return path


# ── PDF 1: Terapi Pertuturan ──
build_pdf(
    "terapi_pertuturan_autism.pdf",
    "Terapi Pertuturan untuk Kanak-kanak Autism",
    [
        ("Pengenalan", [
            "Terapi pertuturan atau speech therapy adalah antara intervensi paling penting untuk kanak-kanak autism. Kanak-kanak autism sering mengalami kelewatan dalam perkembangan bahasa dan komunikasi. Ada yang tidak boleh bercakap langsung, ada yang bercakap tetapi tidak menggunakan ayat dengan betul, dan ada yang bercakap tetapi tidak memahami komunikasi dua hala.",
            "Terapi pertuturan membantu kanak-kanak autism meningkatkan kemahiran komunikasi, sama ada secara lisan, menggunakan gambar (PECS), atau melalui peranti komunikasi augmentatif dan alternatif (AAC).",
        ]),
        ("Matlamat Terapi Pertuturan", [
            "Matlamat utama terapi pertuturan untuk kanak-kanak autism termasuk: meningkatkan kemahiran artikulasi dan sebutan, mengembangkan perbendaharaan kata, mengajar komunikasi dua hala seperti gilir bercakap dan mendengar, serta mengurangkan tingkah laku komunikasi yang mencabar seperti menjerit atau memukul untuk mendapatkan perhatian.",
            "Selain itu, terapi ini juga membantu kanak-kanak autism memahami bahasa bukan lisan seperti gerak badan, mimik muka, dan nada suara yang penting dalam interaksi sosial.",
        ]),
        ("Teknik dalam Terapi Pertuturan", [
            "Antara teknik yang digunakan oleh speech therapist ialah Picture Exchange Communication System (PECS) di mana kanak-kanak menggunakan gambar untuk berkomunikasi. Teknik ini sesuai untuk kanak-kanak yang belum boleh bercakap.",
            "Teknik kedua ialah Augmentative and Alternative Communication (AAC) yang menggunakan peranti elektronik untuk membantu kanak-kanak menyebut perkataan. Peranti ini mempunyai butang dengan gambar dan suara yang kanak-kanak boleh tekan untuk berkomunikasi.",
            "Teknik ketiga ialah floor time atau play-based therapy di mana therapist bermain bersama kanak-kanak dan menggalakkan komunikasi secara semula jadi semasa bermain. Ini membantu kanak-kanak belajar komunikasi dalam konteks yang menyeronokkan.",
        ]),
        ("Tempoh dan Kekerapan", [
            "Kanak-kanak autism memerlukan terapi pertuturan sekurang-kurangnya 2 hingga 3 kali seminggu. Setiap sesi mengambil masa 45 minit hingga 1 jam. Tempoh rawatan bergantung kepada tahap kelewatan bahasa kanak-kanak.",
            "Kanak-kanak yang tidak boleh bercakap langsung mungkin memerlukan terapi selama 2 hingga 3 tahun sebelum mula bercakap dengan lancar. Kanak-kanak yang sudah boleh bercakap tetapi mempunyai masalah sebutan mungkin hanya memerlukan 6 bulan hingga 1 tahun terapi.",
        ]),
        ("Peranan Ibu Bapa di Rumah", [
            "Ibu bapa perlu mengamalkan teknik yang diajar oleh therapist di rumah. Ini termasuk menggunakan gambar untuk berkomunikasi, memberi masa untuk kanak-kanak menjawab soalan, dan tidak mengatasi jawapan kanak-kanak terlalu cepat.",
            "Ibu bapa juga digalakkan membaca buku bersama kanak-kanak setiap hari, menyanyi lagu kanak-kanak, dan bermain permainan yang melibatkan gilir bercakap. Aktiviti ini mengukuhkan kemahiran yang dipelajari semasa sesi terapi.",
        ]),
    ],
)

# ── PDF 2: Tingkah Laku Cabaran ──
build_pdf(
    "tingkah_laku_cabaran_autism.pdf",
    "Pengurusan Tingkah Laku Cabaran pada Kanak-kanak Autism",
    [
        ("Pengenalan", [
            "Kanak-kanak autism sering menunjukkan tingkah laku yang mencabar seperti tantrum, memukul diri sendiri, menggigit, menggaru, melarikan diri, dan merosakkan harta benda. Tingkah laku ini bukan kerana kanak-kanak itu nakal, tetapi merupakan cara mereka berkomunikasi atau mengatasi kekecewaan apabila mereka tidak dapat menyatakan keperluan mereka.",
            "Pengurusan tingkah laku cabaran memerlukan pemahaman tentang fungsi tingkah laku tersebut. Setiap tingkah laku mempunyai sebab, dan tugas therapist serta ibu bapa adalah untuk mencari sebab tersebut dan mengajar cara komunikasi yang lebih baik.",
        ]),
        ("Jenis Tingkah Laku Cabaran", [
            "Tantrum adalah tingkah laku yang paling biasa dilihat. Kanak-kanak mungkin menangis kuat, berguling di lantai, membaling barang, dan menjerit. Tantrum biasanya berlaku apabila kanak-kanak tidak mendapat apa yang mereka mahu atau apabila terdapat perubahan dalam rutin.",
            "Tingkah laku membahayakan diri (self-injurious behavior) termasuk memukul kepala, menggigit tangan, dan menggaru muka. Tingkah laku ini lebih serius dan memerlukan intervensi segera oleh profesional.",
            "Melarikan diri (elopement) berlaku apabila kanak-kanak autism lari dari rumah atau bilik tanpa memberitahu ibu bapa. Ini sangat berbahaya kerana kanak-kanak tidak sedar bahaya seperti jalan raya atau air.",
        ]),
        ("Fungsi Tingkah Laku (FBA)", [
            "Functional Behavior Assessment (FBA) adalah proses untuk mengenal pasti sebab sesuatu tingkah laku berlaku. Terdapat empat fungsi utama: mendapatkan perhatian, mendapatkan barang yang diingini, mengelak tugas yang tidak disukai, dan stimulasi sensori.",
            "Setelah fungsi dikenal pasti, therapist akan membangunkan pelan intervensi yang mengajar kanak-kanak cara baru untuk mencapai tujuan yang sama. Contohnya, jika kanak-kanak menjerit untuk mendapatkan perhatian, therapist akan mengajar kanak-kanak menggunakan gambar atau perkataan untuk meminta perhatian dengan cara yang sesuai.",
        ]),
        ("Strategi Pengurusan", [
            "Strategi pertama ialah pencegahan dengan mengelakkan situasi yang mencetuskan tingkah laku. Contohnya, jika kanak-kanak menjadi marah apabila terlalu banyak orang, elakkan membawa kanak-kanak ke tempat yang sesak.",
            "Strategi kedua ialah pengukuhan positif di mana kanak-kanak diberi ganjaran apabila menunjukkan tingkah laku yang baik. Ganjaran boleh berupa pujian, mainan kegemaran, atau masa bermain tambahan.",
            "Strategi ketiga ialah pengajaran kemahiran pengganti. Jika kanak-kanak memukul diri kerana kecewa, ajar kanak-kanak itu untuk berkata 'saya sedih' atau menggunakan kad gambar untuk menyatakan perasaan.",
            "Strategi keempat ialah respon yang konsisten. Semua ahli keluarga dan guru perlu memberi respon yang sama kepada tingkah laku kanak-kanak. Jika ibu bapa tidak konsisten, kanak-kanak akan keliru dan tingkah laku akan berterusan.",
        ]),
        ("Bila Perlu Bantuan Profesional", [
            "Ibu bapa harus mencari bantuan profesional apabila tingkah laku kanak-kanak membahayakan diri sendiri atau orang lain, apabila tingkah laku berterusan walaupun selepas 4 minggu cubaan pengurusan di rumah, atau apabila tingkah laku menjejaskan kehidupan harian keluarga secara serius.",
            "Profesional yang boleh membantu termasuk behavior analyst, clinical psychologist, dan occupational therapist. Mereka akan menjalankan penilaian dan membangunkan pelan intervensi yang khusus untuk kanak-kanak tersebut.",
        ]),
    ],
)

# ── PDF 3: Terapi Pemakanan ──
build_pdf(
    "terapi_pemakanan_autism.pdf",
    "Terapi Pemakanan untuk Kanak-kanak Autism",
    [
        ("Pengenalan", [
            "Masalah pemakanan adalah antara cabaran yang paling biasa dihadapi oleh kanak-kanak autism. Kajian menunjukkan bahawa 70% hingga 90% kanak-kanak autism mempunyai masalah pemakanan, termasuk pemilih makanan yang teruk (picky eating), kepekaan terhadap tekstur dan bau makanan, serta tingkah laku makan yang tidak biasa seperti memakan bahan bukan makanan (pica).",
            "Terapi pemakanan atau feeding therapy bertujuan untuk membantu kanak-kanak autism menerima pelbagai jenis makanan, mengurangkan kekecewaan semasa waktu makan, dan memastikan kanak-kanak mendapat nutrisi yang mencukupi untuk tumbesaran yang sihat.",
        ]),
        ("Jenis Masalah Pemakanan", [
            "Pemilih makanan yang teruk bermaksud kanak-kanak hanya mahu makan satu jenis makanan atau makanan dengan warna, tekstur, dan jenama yang sama. Contohnya, kanak-kanak hanya mahu makan nasi putih dengan satu jenama sos tertentu. Sekiranya jenama itu ditukar, kanak-kanak akan menolak makanan tersebut.",
            "Kepekaan sensori terhadap makanan menyebabkan kanak-kanak autism menolak makanan berdasarkan tekstur, suhu, bau, atau rupa. Makanan yang lembut, makanan yang rangup, makanan yang sejuk, atau makanan yang bercampur boleh menyebabkan kanak-kanak autism menolak makanan tersebut.",
            "Pica adalah keadaan di mana kanak-kanak memakan bahan bukan makanan seperti kertas, tanah, kapur, atau rambut. Ini berbahaya kerana boleh menyebabkan keracunan atau halangan usus dan memerlukan rawatan perubatan segera.",
        ]),
        ("Punca Masalah Pemakanan", [
            "Kepekaan sensori adalah punca utama. Kanak-kanak autism mempunyai kepekaan deria yang berbeza dari kanak-kanak biasa. Makanan yang kita rasa sedap mungkin terasa terlalu kuat atau menyakitkan bagi mereka.",
            "Kebimbangan dan keperluan rutin juga menyumbang kepada masalah pemakanan. Kanak-kanak autism memerlukan rutin yang sama setiap hari. Sebarang perubahan dalam jenis makanan, tempat makan, atau alat makan boleh menyebabkan kekecewaan yang teruk.",
            "Masalah motorik oral seperti kelemahan otot mulut dan lidah boleh menyebabkan kesukaran mengunyah dan menelan. Ini membuatkan kanak-kanak mengelak makanan yang sukar dikunyah seperti daging dan sayur-sayuran keras.",
        ]),
        ("Strategi Rawatan", [
            "SOS Approach to Feeding adalah pendekatan yang paling berkesan untuk kanak-kanak autism. Terapi ini memperkenalkan makanan baru secara berperingkat, bermula dengan melihat makanan dari jauh, kemudian menyentuh, mencium, mencium, menyentuh bibir, menjilat, menggigit, dan akhirnya memakan.",
            "Food chaining adalah teknik di mana makanan baru diperkenalkan secara beransur-ansur bermula dari makanan yang kanak-kanak sudah suka. Contohnya, jika kanak-kanak suka keropok, kita perkenalkan keropok rasa keju, kemudian keju betul, kemudian keju dengan roti, dan seterusnya.",
            "Pengurusan sensori melibatkan penyesuaian persekitaran makan. Gunakan pinggan yang sama setiap hari, pastikan makanan tidak bercampur, dan hidangkan makanan pada suhu yang sama. Beberapa kanak-kanak autism memerlukan makanan dipisahkan dalam bahagian yang berbeza.",
            "Terapi pertuturan dan occupational therapy juga boleh membantu dengan menguatkan otot mulut dan mengajar kemahiran mengunyah dan menelan dengan betul.",
        ]),
        ("Pemantauan Pertumbuhan", [
            "Kanak-kanak autism yang mempunyai masalah pemakanan memerlukan pemantauan pertumbuhan yang kerap oleh doktor atau dietitian. Berat dan tinggi badan perlu direkod setiap bulan untuk memastikan kanak-kanak tidak mengalami kekurangan zat makanan.",
            "Sekiranya kanak-kanak tidak menambah berat badan selama 3 bulan berturut-turut, rujukan kepada dietitian atau pakar pemakanan diperlukan. Mereka mungkin mengesyorkan suplemen pemakanan untuk memastikan keperluan nutrisi kanak-kanak dipenuhi.",
        ]),
    ],
)

print("\nAll 3 PDFs generated successfully.")
