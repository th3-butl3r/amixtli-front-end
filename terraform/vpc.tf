# ────────────────────────────────────────────────────────────
#  vpc.tf - Cloud Private Network para el manejo del servicio
# ────────────────────────────────────────────────────────────

resource "aws_vpc" "nuestroentorno" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}

# ── Subred pública ───────────────────────────────────────────────
resource "aws_subnet" "public_nuestroentorno" {
  vpc_id                  = aws_vpc.nuestroentorno.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
}

# ── Internet Gateway ─────────────────────────────────────────────
/*
¿Para qué sirve el Internet Gateway?

Es la puerta de salida de tu VPC hacia internet.
Sin él, los recursos dentro de la VPC están completamente aislados
no pueden conectarse a Supabase, no pueden descargar la imagen de ECR,
nadie puede entrar.
Es literalmente el cable que conecta tu red privada con internet.
*/
resource "aws_internet_gateway" "nuestroentorno" {
  vpc_id = aws_vpc.nuestroentorno.id
}

# ── Tabla de rutas ───────────────────────────────────────────────
/*
¿Para qué sirve la Route Table?
El Internet Gateway existe, pero los recursos no saben que existe.
La Route Table es el mapa de rutas que le dice a cada paquete de red
hacia dónde ir:
Destino        → Por dónde
10.0.0.0/16   → Dentro de la VPC (local, automático)
0.0.0.0/0     → Internet Gateway (cualquier otra cosa)

*/
resource "aws_route_table" "public_nuestroentorno" {
  vpc_id = aws_vpc.nuestroentorno.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.nuestroentorno.id
  }
}

resource "aws_route_table_association" "public_nuestroentorno" {
  subnet_id      = aws_subnet.public_nuestroentorno.id
  route_table_id = aws_route_table.public_nuestroentorno.id
}

# ── Security Group ───────────────────────────────────────────────
/*
El Security Group es el firewall de tu contenedor.

Controla exactamente qué tráfico puede entrar y qué puede salir.
Cada recurso en AWS (contenedor, EC2, RDS, etc.) debe tener al menos un Security Group asociado.

Tiene dos tipos de reglas:
ingress - tráfico de entrada
en nuestro caso:

ingress {
  from_port   = 8080
  to_port     = 8080
  protocol    = "tcp"
  cidr_blocks = [ ...IPs de Cloudflare... ]
}

Traducido: "solo permite entrada en el puerto 8080, y únicamente desde las IPs de Cloudflare".

Si alguien intenta conectarse directamente a la IP pública de tu contenedor desde su casa,
AWS lo bloquea antes de que llegue a Flask. Solo Cloudflare puede hablar con tu app.

egress - tráfico de salida

egress {
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
}

Traducido: "el contenedor puede conectarse a cualquier destino".

Necesario para que Flask pueda llamar a Supabase, y para que ECS pueda descargar
la imagen de ECR al arrancar.

LA RELACIÓN CON LOS DEMÁS COMPONENTES
Internet
    │
    ▼
Internet Gateway      ← la puerta de entrada a la VPC
    │
    ▼
Route Table           ← el mapa que dirige el tráfico
    │
    ▼
Security Group        ← el guardia que decide quién pasa
    │
    ▼
Contenedor (puerto 8080)

Sin el Security Group el contenedor estaría expuesto a todo internet.
Con él, solo Cloudflare puede tocarlo.

*/
resource "aws_security_group" "nuestroentorno" {
  name   = "${var.project_name}-sg"
  vpc_id = aws_vpc.nuestroentorno.id

  ingress {
    description = "Trafico desde Cloudflare unicamente"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [
      "173.245.48.0/20",
      "103.21.244.0/22",
      "103.22.200.0/22",
      "103.31.4.0/22",
      "141.101.64.0/18",
      "108.162.192.0/18",
      "190.93.240.0/20",
      "188.114.96.0/20",
      "197.234.240.0/22",
      "198.41.128.0/17",
      "162.158.0.0/15",
      "104.16.0.0/13",
      "104.24.0.0/14",
      "172.64.0.0/13",
      "131.0.72.0/22",
    ]
  }

  egress {
    description = "Salida libre para conectarse a Supabase y ECR"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
