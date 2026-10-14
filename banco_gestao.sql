-- --------------------------------------------------------
-- Servidor:                     127.0.0.1
-- Versão do servidor:           12.3.2-MariaDB - MariaDB Server
-- OS do Servidor:               Win64
-- HeidiSQL Versão:              12.21.0.7344
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Copiando estrutura para tabela gestao_engenharia.linha_responsaveis
CREATE TABLE IF NOT EXISTS `linha_responsaveis` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `linha_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `papel` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `linha_id` (`linha_id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `1` FOREIGN KEY (`linha_id`) REFERENCES `linhas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Copiando dados para a tabela gestao_engenharia.linha_responsaveis: ~0 rows (aproximadamente)
INSERT INTO `linha_responsaveis` (`id`, `linha_id`, `usuario_id`, `papel`) VALUES
	(1, 1, 1, 'Engenharia'),
	(2, 1, 3, 'Produção'),
	(3, 1, 2, 'Qualidade'),
	(4, 1, 1, 'Manutenção'),
	(5, 2, 2, 'Engenharia'),
	(6, 2, 3, 'Produção'),
	(7, 2, 1, 'Qualidade'),
	(8, 2, 2, 'Manutenção'),
	(9, 2, 2, 'Dispositivo');

-- Copiando estrutura para tabela gestao_engenharia.linhas
CREATE TABLE IF NOT EXISTS `linhas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) NOT NULL,
  `codigo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Copiando dados para a tabela gestao_engenharia.linhas: ~0 rows (aproximadamente)
INSERT INTO `linhas` (`id`, `nome`, `codigo`) VALUES
	(1, 'Tampa VW', '34017016'),
	(2, 'Biela VW', '62');

-- Copiando estrutura para tabela gestao_engenharia.tipos_acao
CREATE TABLE IF NOT EXISTS `tipos_acao` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) NOT NULL,
  `tipo_intervencao` varchar(50) NOT NULL,
  `responsavel_padrao_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `responsavel_padrao_id` (`responsavel_padrao_id`),
  CONSTRAINT `1` FOREIGN KEY (`responsavel_padrao_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Copiando dados para a tabela gestao_engenharia.tipos_acao: ~0 rows (aproximadamente)
INSERT INTO `tipos_acao` (`id`, `nome`, `tipo_intervencao`, `responsavel_padrao_id`) VALUES
	(1, 'Documentação', 'Revisar', NULL),
	(2, 'FMEA', 'Revisar', 2),
	(3, 'OEE', 'Atualizar', 1),
	(4, 'TPM', 'Atualizar', NULL);

-- Copiando estrutura para tabela gestao_engenharia.usuarios
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) NOT NULL,
  `login` varchar(50) DEFAULT NULL,
  `senha` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `setor` varchar(100) DEFAULT NULL,
  `area` varchar(100) DEFAULT NULL,
  `cargo` varchar(100) DEFAULT NULL,
  `perfil` varchar(50) DEFAULT 'Operador',
  PRIMARY KEY (`id`),
  UNIQUE KEY `login` (`login`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- Copiando dados para a tabela gestao_engenharia.usuarios: ~0 rows (aproximadamente)
INSERT INTO `usuarios` (`id`, `nome`, `login`, `senha`, `email`, `setor`, `area`, `cargo`, `perfil`) VALUES
	(1, 'Eric Aran', NULL, NULL, 'ericsj@whbbrasil.com.br', 'Engenharia', NULL, NULL, 'Admin'),
	(2, 'Tarcisio Ferreira', NULL, NULL, 'tarcisiosb@whbbrasil.com.br', 'Engenharia', NULL, NULL, 'Operador'),
	(3, 'Hugo', NULL, NULL, '', 'Produção', NULL, NULL, 'Operador'),
	(4, 'Administrador', NULL, NULL, 'admin@empresa.com', 'Engenharia', NULL, NULL, 'Admin'),
	(9, 'Administrador', 'admin', 'admin123', 'admin@whbbrasil.com.br', 'Engenharia', 'Engenharia de Processos', 'Administrador de Sistema', 'Admin'),
	(10, 'Eric Aran Salomão ', 'ericsj', '$2b$12$Whhg///zwqcpWC56Cgl7NefSZYFpMjHm4xD7tgvlNGAnP73vQjY2e', 'ericsj@whbbrasil.com.br', 'Engenharia', 'Processos', 'Analista de processos', 'Admin');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
