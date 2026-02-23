-- Generado automaticamente desde PLAN INDICATIVO 2024 - 2027 PROCESADO.xlsx (hoja DATOS)
-- Registros fuente: 411
ALTER TABLE meta
ADD COLUMN IF NOT EXISTS unidad_medida TEXT;

CREATE TEMP TABLE tmp_meta_unidad_medida (
    numero_meta INT NOT NULL,
    codigo_producto INT NOT NULL,
    codigo_indicador_producto INT NOT NULL,
    unidad_medida TEXT NOT NULL
) ON COMMIT DROP;

INSERT INTO tmp_meta_unidad_medida (numero_meta, codigo_producto, codigo_indicador_producto, unidad_medida) VALUES
    (1, 2201006, 220100602, 'Número'),
    (2, 2201037, 220103701, 'Número'),
    (3, 2201034, 220103400, 'Número'),
    (4, 2201056, 220105600, 'Número'),
    (5, 2201061, 220106100, 'Número'),
    (6, 2201067, 220106700, 'Número'),
    (7, 2201073, 220107300, 'Número'),
    (8, 2201074, 220107400, 'Número'),
    (9, 2201081, 220108100, 'Número'),
    (10, 2201084, 220108400, 'Número'),
    (11, 2201085, 220108500, 'Número'),
    (12, 2301035, 230103500, 'Número'),
    (13, 2201047, 220104700, 'Número'),
    (14, 2202062, 220206200, 'Número'),
    (15, 2202065, 220206500, 'Número'),
    (16, 2202072, 220207200, 'Número'),
    (17, 2301062, 230106200, 'Número'),
    (18, 2301062, 230106200, 'Número'),
    (19, 2201070, 220107000, 'Número'),
    (20, 2201015, 220101500, 'Número'),
    (21, 2201017, 220101700, 'Número'),
    (22, 2201017, 220101700, 'Número'),
    (23, 2201017, 220101700, 'Número'),
    (24, 2201017, 220101700, 'Número'),
    (25, 2201017, 220101700, 'Número'),
    (26, 2201052, 220105200, 'Número'),
    (27, 2201039, 220103900, 'Número'),
    (28, 2201002, 220100200, 'Número'),
    (29, 2201069, 220106900, 'Número'),
    (30, 2201049, 220104900, 'Número'),
    (31, 2201017, 220101700, 'Número'),
    (32, 2201082, 220108200, 'Número'),
    (33, 2201068, 220106800, 'Número'),
    (34, 2201055, 220105500, 'Número'),
    (35, 2201079, 220107900, 'Número'),
    (36, 2201089, 220108900, 'Número'),
    (37, 2201030, 220103000, 'Número'),
    (38, 2201032, 220103200, 'Número'),
    (39, 2201017, 220101700, 'Número'),
    (40, 3301126, 330112600, 'Número'),
    (41, 3301074, 330107400, 'Número'),
    (42, 3301065, 330106500, 'Número'),
    (43, 3301073, 330107300, 'Número'),
    (44, 3301053, 330105300, 'Número'),
    (45, 3301051, 330105100, 'Número'),
    (46, 3301099, 330109900, 'Número'),
    (47, 3301129, 330112900, 'Número'),
    (48, 3302049, 330204900, 'Número'),
    (49, 3502004, 350200400, 'Número'),
    (50, 3502019, 350201900, 'Número'),
    (51, 1906044, 190604400, 'Número'),
    (52, 1905027, 190502700, 'Número'),
    (53, 1905054, 190505403, 'Número'),
    (54, 1905054, 190505400, 'Número'),
    (55, 1905050, 190505000, 'Número'),
    (56, 1905054, 190505400, 'Número'),
    (57, 1905054, 190505404, 'Número'),
    (58, 1905054, 190505404, 'Número'),
    (59, 1905054, 190505405, 'Número'),
    (60, 1905054, 190505400, 'Número'),
    (61, 1905054, 190505400, 'Número'),
    (62, 1905054, 190505408, 'Número'),
    (63, 1903057, 190305700, 'Número'),
    (64, 1903047, 190304700, 'Número'),
    (65, 1903057, 190305700, 'Número'),
    (66, 1903057, 190305700, 'Número'),
    (67, 1905031, 190503102, 'Número'),
    (68, 1906029, 190602900, 'Número'),
    (69, 1905008, 190500800, 'Número'),
    (70, 1905030, 190503000, 'Número'),
    (71, 1905026, 190502602, 'Número'),
    (72, 1905026, 190502602, 'Número'),
    (73, 1905043, 190504302, 'Número'),
    (74, 1903057, 190305700, 'Número'),
    (75, 1905043, 190504300, 'Número'),
    (76, 1905054, 190505411, 'Número'),
    (77, 1905043, 190504302, 'Número'),
    (78, 1905046, 190504600, 'Número'),
    (79, 1905046, 190504601, 'Número'),
    (80, 1905048, 190504800, 'Número'),
    (81, 1903012, 190301200, 'Número'),
    (82, 1903023, 190302300, 'Número'),
    (83, 1905050, 190505000, 'Número'),
    (84, 1903052, 190305200, 'Número'),
    (85, 1905053, 190505300, 'Número'),
    (86, 1905053, 190505300, 'Número'),
    (87, 1905053, 190505300, 'Número'),
    (88, 1905053, 190505300, 'Número'),
    (89, 1906029, 190602900, 'Número'),
    (90, 1903011, 190301100, 'Número'),
    (91, 1906029, 190602900, 'Número'),
    (92, 1906004, 190600400, 'Porcentaje'),
    (93, 1905050, 190505000, 'Número'),
    (94, 1906040, 190604000, 'Número'),
    (95, 1906041, 190604100, 'Número'),
    (96, 1906041, 190604100, 'Número'),
    (97, 1906041, 190604100, 'Número'),
    (98, 1906027, 190602700, 'Número'),
    (99, 1906026, 190602601, 'Número'),
    (100, 1906022, 190602200, 'Número'),
    (101, 1906034, 190603400, 'Número'),
    (102, 1906030, 190603000, 'Número'),
    (103, 1906001, 190600100, 'Número'),
    (104, 1906002, 190600200, 'Número'),
    (105, 1906003, 190600300, 'Número'),
    (106, 1906011, 190601100, 'Número'),
    (107, 1906009, 190600900, 'Número'),
    (108, 1906016, 190601600, 'Número'),
    (109, 4599008, 459900800, 'Número'),
    (110, 1906034, 190603400, 'Número'),
    (111, 1903016, 190301600, 'Número'),
    (112, 1903011, 190301100, 'Número'),
    (113, 1903027, 190302700, 'Número'),
    (114, 1903019, 190301900, 'Porcentaje'),
    (115, 1903045, 190304500, 'Número'),
    (116, 1903001, 190300103, 'Número'),
    (117, 1903023, 190302300, 'Número'),
    (118, 1905054, 190505400, 'Número'),
    (119, 1905054, 190505400, 'Número'),
    (120, 1903012, 190301200, 'Número'),
    (121, 1903012, 190301200, 'Número'),
    (122, 4301001, 430100100, 'Número'),
    (123, 4301037, 430103700, 'Número'),
    (124, 4301007, 430100700, 'Número'),
    (125, 4302001, 430200100, 'Número'),
    (126, 4302002, 430200200, 'Número'),
    (127, 4302062, 430206200, 'Número'),
    (128, 1702007, 170200700, 'Número'),
    (129, 406001, 40600100, 'Número'),
    (130, 1702038, 170203800, 'Número'),
    (131, 1707018, 170701800, 'Número'),
    (132, 1702035, 170203500, 'Número'),
    (133, 1708041, 170804100, 'Número'),
    (134, 1702009, 170200900, 'Número'),
    (135, 1702014, 170201401, 'Número'),
    (136, 1709013, 170901300, 'Número'),
    (137, 1709065, 170906500, 'Número'),
    (138, 1709106, 170910600, 'Número'),
    (139, 1704003, 170400300, 'Número'),
    (140, 3906009, 390600900, 'Número'),
    (141, 2301030, 230103000, 'Número'),
    (142, 4501004, 450100400, 'Número'),
    (143, 1704014, 170401400, 'Número'),
    (144, 4103051, 410305100, 'Número'),
    (145, 1708002, 170800200, 'Número'),
    (146, 2201061, 220106100, 'Número'),
    (147, 1709059, 170905900, 'Número'),
    (148, 4103060, 410306000, 'Número'),
    (149, 4599032, 459903200, 'Número'),
    (150, 4103055, 410305500, 'Número'),
    (151, 1702032, 170203200, 'Número'),
    (152, 1709025, 170902500, 'Número'),
    (153, 3202045, 320204500, 'Número'),
    (154, 3202043, 320204300, 'Número'),
    (155, 3208006, 320800600, 'Número'),
    (156, 3205006, 320500600, 'Número'),
    (157, 3202003, 320200300, 'Número'),
    (158, 4501061, 450106100, 'Número'),
    (159, 3206004, 320600400, 'Número'),
    (160, 3202041, 320204100, 'Número'),
    (161, 3206016, 320601600, 'Número'),
    (162, 2102058, 210205800, 'Número'),
    (163, 1702007, 170200700, 'Número'),
    (164, 4503002, 450300200, 'Número'),
    (165, 4503003, 450300300, 'Número'),
    (166, 4503004, 450300400, 'Número'),
    (167, 4503016, 450301600, 'Número'),
    (168, 4503016, 450301600, 'Número'),
    (169, 4503018, 450301800, 'Número'),
    (170, 4503023, 450302302, 'Número'),
    (171, 4503022, 450302200, 'Número'),
    (172, 4503023, 450302300, 'Número'),
    (173, 4503024, 450302400, 'Número'),
    (174, 4503028, 450302800, 'Número'),
    (175, 3206003, 320600300, 'Número'),
    (176, 3206004, 320600400, 'Número'),
    (177, 3206008, 320600800, 'Número'),
    (178, 3906015, 390601500, 'Número'),
    (179, 3905002, 390500200, 'Número'),
    (180, 3905005, 390500500, 'Número'),
    (181, 3905007, 390500700, 'Número'),
    (182, 3906011, 390601100, 'Número'),
    (183, 3906005, 390600500, 'Número'),
    (184, 3906006, 390600600, 'Número'),
    (185, 3906019, 390601900, 'Número'),
    (186, 3906009, 390600900, 'Número'),
    (187, 3502017, 350201700, 'Número'),
    (188, 4103059, 410305900, 'Número'),
    (189, 3602032, 360203200, 'Número'),
    (190, 3604016, 360401600, 'Número'),
    (191, 2104010, 210401000, 'Número'),
    (192, 3502036, 350203600, 'Número'),
    (193, 3502114, 350211400, 'Número'),
    (194, 3502039, 350203900, 'Número'),
    (195, 3502045, 350204500, 'Número'),
    (196, 3502046, 350204600, 'Número'),
    (197, 3502093, 350209300, 'Número'),
    (198, 3502047, 350204700, 'Número'),
    (199, 3502049, 350204900, 'Número'),
    (200, 3502110, 350211000, 'Número'),
    (201, 3502017, 350201703, 'Número'),
    (202, 3502047, 350204700, 'Número'),
    (203, 3502010, 350201000, 'Número'),
    (204, 4103059, 410305900, 'Número'),
    (205, 3502007, 350200700, 'Número'),
    (206, 3502008, 350200800, 'Número'),
    (207, 3502004, 350200400, 'Número'),
    (208, 3502009, 350200900, 'Número'),
    (209, 3502021, 350202100, 'Número'),
    (210, 3502022, 350202200, 'Número'),
    (211, 3502006, 350200600, 'Número'),
    (212, 3502002, 350200200, 'Número'),
    (213, 3602027, 360202700, 'Número'),
    (214, 3602003, 360200300, 'Número'),
    (215, 2104012, 210401200, 'Número'),
    (216, 2104018, 210401800, 'Número'),
    (217, 2104022, 210402200, 'Número'),
    (218, 2104027, 210402700, 'Número'),
    (219, 4599025, 459902500, 'Número'),
    (220, 3502112, 350211200, 'Número'),
    (221, 4001042, 400104200, 'Número'),
    (222, 4001044, 400104400, 'Número'),
    (223, 2401009, 240100900, 'Kilómetros'),
    (224, 2402001, 240200100, 'Kilómetros'),
    (225, 2402006, 240200600, 'Kilómetros'),
    (226, 2402018, 240201800, 'Kilómetros'),
    (227, 2402021, 240202101, 'Kilómetros'),
    (228, 2402035, 240203500, 'Kilómetros'),
    (229, 2402038, 240203800, 'Número'),
    (230, 2402041, 240204100, 'Kilómetros'),
    (231, 2402112, 240211200, 'Kilómetros'),
    (232, 2402096, 240209600, 'Kilómetros'),
    (233, 2402098, 240209800, 'Número'),
    (234, 2402114, 240211400, 'Kilómetros'),
    (235, 2402015, 240201500, 'Número'),
    (236, 2402019, 240201900, 'Número'),
    (237, 2402022, 240202200, 'Número'),
    (238, 2402044, 240204400, 'Número'),
    (239, 2402046, 240204600, 'Número'),
    (240, 2402048, 240204800, 'Número'),
    (241, 2402051, 240205100, 'Número'),
    (242, 2402119, 240211900, 'Número'),
    (243, 2402118, 240211800, 'Número'),
    (244, 2402028, 240202800, 'Kilómetros'),
    (245, 2402049, 240204900, 'Kilómetros'),
    (246, 2102045, 210204500, 'Número'),
    (247, 2102058, 210205800, 'Número'),
    (248, 2102033, 210203300, 'Número'),
    (249, 2102062, 210206201, 'MW'),
    (250, 2101016, 210101600, 'Número'),
    (251, 2102069, 210206900, 'Número'),
    (252, 4301031, 430103100, 'Número'),
    (253, 4301014, 430101400, 'Número'),
    (254, 4301018, 430101800, 'Número'),
    (255, 4302028, 430202800, 'Número'),
    (256, 4302025, 430202500, 'Número'),
    (257, 4302015, 430201500, 'Número'),
    (258, 4302074, 430207400, 'Número'),
    (259, 4302010, 430201000, 'Número'),
    (260, 4301025, 430102500, 'Número'),
    (261, 4301029, 430102900, 'Número'),
    (262, 1709078, 170907800, 'Número'),
    (263, 4003017, 400301700, 'Número'),
    (264, 4003015, 400301500, 'Número'),
    (265, 4003015, 400301500, 'Número'),
    (266, 4003042, 400304200, 'Número'),
    (267, 4003015, 400301500, 'Número'),
    (268, 4003016, 400301600, 'Número'),
    (269, 4003017, 400301700, 'Número'),
    (270, 4003018, 400301800, 'Número'),
    (271, 4003019, 400301900, 'Número'),
    (272, 4003020, 400302000, 'Número'),
    (273, 4003018, 400301800, 'Número'),
    (274, 4003019, 400301900, 'Número'),
    (275, 4003020, 400302000, 'Número'),
    (276, 4003010, 400301000, 'Número'),
    (277, 4003010, 400301000, 'Número'),
    (278, 4003031, 400303100, 'Número'),
    (279, 4003010, 400301000, 'Número'),
    (280, 4003052, 400305200, 'Número'),
    (281, 4003055, 400305500, 'Número'),
    (282, 4003053, 400305300, 'Número'),
    (283, 45020030, 450203000, 'Número'),
    (284, 4502022, 450202200, 'Número'),
    (285, 4502034, 450203400, 'Número'),
    (286, 4502033, 450203300, 'Número'),
    (287, 4599032, 459903200, 'Número'),
    (288, 4502016, 450201600, 'Número'),
    (289, 4502001, 450200100, 'Número'),
    (290, 4502022, 450202200, 'Número'),
    (291, 4502008, 450200800, 'Número'),
    (292, 4599032, 459903200, 'Número'),
    (293, 4502025, 450202500, 'Número'),
    (294, 4502024, 450202400, 'Número'),
    (295, 4501003, 450100300, 'Número'),
    (296, 4501031, 450103100, 'Número'),
    (297, 4599025, 459902500, 'Número'),
    (298, 4501026, 450102600, 'Número'),
    (299, 4501026, 450102600, 'Número'),
    (300, 4501031, 450103100, 'Número'),
    (301, 4501044, 450104400, 'Número'),
    (302, 4501001, 450100100, 'Número'),
    (303, 4501004, 450100400, 'Número'),
    (304, 1202019, 120201900, 'Número'),
    (305, 4101092, 410109200, 'Número'),
    (306, 4101074, 410107400, 'Número'),
    (307, 4101027, 410102700, 'Porcentaje'),
    (308, 4101038, 410103800, 'Número'),
    (309, 4101038, 410103800, 'Número'),
    (310, 4101023, 410102300, 'Número'),
    (311, 4101047, 410104700, 'Número'),
    (312, 4101025, 410102500, 'Número'),
    (313, 4501049, 450104900, 'Número'),
    (314, 4599031, 459903100, 'Número'),
    (315, 4501026, 450102600, 'Número'),
    (316, 4599017, 459901700, 'Número'),
    (317, 4103058, 410305800, 'Número'),
    (318, 4103059, 410305900, 'Número'),
    (319, 4502001, 450200100, 'Número'),
    (320, 4102045, 410204500, 'Número'),
    (321, 4102040, 410204000, 'Número'),
    (322, 4102047, 410204700, 'Número'),
    (323, 4301037, 430103700, 'Número'),
    (324, 4104002, 410400200, 'Número'),
    (325, 4104008, 410400800, 'Número'),
    (326, 4104022, 410402200, 'Número'),
    (327, 4104023, 410402300, 'Número'),
    (328, 4502035, 450203500, 'Número'),
    (329, 4103017, 410301700, 'Número'),
    (330, 4103055, 410305500, 'Número'),
    (331, 4103057, 410305700, 'Número'),
    (332, 4599032, 459903200, 'Número'),
    (333, 4502033, 450203300, 'Número'),
    (334, 4102003, 410200300, 'Número'),
    (335, 4102041, 410204100, 'Número'),
    (336, 4102047, 410204700, 'Número'),
    (337, 4102046, 410204600, 'Número'),
    (338, 4502033, 450203300, 'Número'),
    (339, 4102043, 410204300, 'Número'),
    (340, 4103052, 410305200, 'Número'),
    (341, 4104020, 410402000, 'Número'),
    (342, 4502033, 450203300, 'Número'),
    (343, 4502038, 450203800, 'Número'),
    (344, 4502001, 450200100, 'Número'),
    (345, 4599001, 459900100, 'Número'),
    (346, 4501004, 450100400, 'Número'),
    (347, 1702007, 170200700, 'Número'),
    (348, 1702011, 170201100, 'Número'),
    (349, 3502036, 350203600, 'Número'),
    (350, 3602003, 360200300, 'Número'),
    (351, 4501007, 450100700, 'Número'),
    (352, 3602027, 360202700, 'Número'),
    (353, 3602002, 360200200, 'Número'),
    (354, 1704017, 170401700, 'Número'),
    (355, 1202020, 120202000, 'Número'),
    (356, 4101079, 410107900, 'Número'),
    (357, 4502024, 450202400, 'Número'),
    (358, 4502024, 450202400, 'Número'),
    (359, 4501050, 450105000, 'Número'),
    (360, 4102042, 410204200, 'Número'),
    (361, 190502, 190502000, 'Número'),
    (362, 4501049, 450104900, 'Número'),
    (363, 4501049, 450104900, 'Número'),
    (364, 4502024, 450202400, 'Número'),
    (365, 4502037, 450203700, 'Número'),
    (366, 4502020, 450202000, 'Número'),
    (367, 1905021, 190502100, 'Número'),
    (368, 1905019, 190501900, 'Número'),
    (369, 1905021, 190502100, 'Número'),
    (370, 1905019, 190501900, 'Número'),
    (371, 4502022, 450202200, 'Número'),
    (372, 4502038, 450203800, 'Número'),
    (373, 4502035, 450203500, 'Número'),
    (374, 1202030, 120203000, 'Número'),
    (375, 1202030, 120203000, 'Número'),
    (376, 1202019, 120201900, 'Número'),
    (377, 1702017, 170201700, 'Número'),
    (378, 3208006, 320800600, 'Número'),
    (379, 3906001, 390600100, 'Número'),
    (380, 2202065, 220206500, 'Número'),
    (381, 4502001, 450200100, 'Número'),
    (382, 4502034, 450203400, 'Número'),
    (383, 4502022, 450202200, 'Número'),
    (384, 4599028, 459902800, 'Número'),
    (385, 4599032, 459903200, 'Número'),
    (386, 4599002, 459900200, 'Porcentaje'),
    (387, 4599018, 459901800, 'Número'),
    (388, 4599019, 459901900, 'Número'),
    (389, 4599023, 459902300, 'Número'),
    (390, 4599031, 459903100, 'Número'),
    (391, 4001001, 400100100, 'Número'),
    (392, 4001007, 400100700, 'Número'),
    (393, 4599023, 459902300, 'Número'),
    (394, 4599017, 459901700, 'Número'),
    (395, 4599008, 459900800, 'Número'),
    (396, 4599012, 459901200, 'Número'),
    (397, 4599016, 459901600, 'Número'),
    (398, 4599020, 459902000, 'Número'),
    (399, 4599029, 459902900, 'Número'),
    (400, 4502001, 450200100, 'Número'),
    (401, 4502013, 450201300, 'Número'),
    (402, 4599030, 459903000, 'Número'),
    (403, 4599038, 459903800, 'Número'),
    (404, 4599011, 459901100, 'Número'),
    (405, 4599020, 459902000, 'Número'),
    (406, 2302061, 230206100, 'Número'),
    (407, 2302078, 230207800, 'Número'),
    (408, 4599005, 459900500, 'Número'),
    (409, 4599007, 459900700, 'Porcentaje'),
    (410, 2302036, 230203600, 'Número'),
    (411, 4599023, 459902300, 'Número');

-- Validaciones de seguridad: claves ?nicas en destino y coincidencia completa con fuente
DO $$
DECLARE
    v_dup_target INT;
    v_missing_target INT;
    v_expected INT;
BEGIN
    SELECT COUNT(*) INTO v_expected FROM tmp_meta_unidad_medida;

    SELECT COUNT(*) INTO v_dup_target
    FROM (
        SELECT m.numero_meta, m.codigo_producto, m.codigo_indicador_producto
        FROM meta m
        JOIN tmp_meta_unidad_medida t
          ON t.numero_meta = m.numero_meta
         AND t.codigo_producto = m.codigo_producto
         AND t.codigo_indicador_producto = m.codigo_indicador_producto
        GROUP BY m.numero_meta, m.codigo_producto, m.codigo_indicador_producto
        HAVING COUNT(*) > 1
    ) q;

    IF v_dup_target > 0 THEN
        RAISE EXCEPTION 'Hay claves duplicadas en tabla meta para las claves del plan indicativo (%). Abortado.', v_dup_target;
    END IF;

    SELECT COUNT(*) INTO v_missing_target
    FROM tmp_meta_unidad_medida t
    LEFT JOIN meta m
      ON t.numero_meta = m.numero_meta
     AND t.codigo_producto = m.codigo_producto
     AND t.codigo_indicador_producto = m.codigo_indicador_producto
    WHERE m.id IS NULL;

    IF v_missing_target > 0 THEN
        RAISE EXCEPTION 'Hay % claves del plan indicativo sin coincidencia en meta. Abortado.', v_missing_target;
    END IF;
END $$;

UPDATE meta m
SET unidad_medida = t.unidad_medida
FROM tmp_meta_unidad_medida t
WHERE t.numero_meta = m.numero_meta
  AND t.codigo_producto = m.codigo_producto
  AND t.codigo_indicador_producto = m.codigo_indicador_producto;

DO $$
DECLARE
    v_expected INT;
    v_loaded_ok INT;
BEGIN
    SELECT COUNT(*) INTO v_expected FROM tmp_meta_unidad_medida;
    SELECT COUNT(*) INTO v_loaded_ok
    FROM meta m
    JOIN tmp_meta_unidad_medida t
      ON t.numero_meta = m.numero_meta
     AND t.codigo_producto = m.codigo_producto
     AND t.codigo_indicador_producto = m.codigo_indicador_producto
    WHERE COALESCE(m.unidad_medida, '') = t.unidad_medida;

    IF v_loaded_ok <> v_expected THEN
        RAISE EXCEPTION 'Validaci?n final fall?: % de % filas quedaron con unidad_medida correcta.', v_loaded_ok, v_expected;
    END IF;
END $$;

-- SELECT COUNT(*) AS metas_con_unidad FROM meta WHERE COALESCE(TRIM(unidad_medida), '') <> '';

-- Recarga completa de meta (propuesta): preserva IDs y restaura relaciones en metas
-- Seguridad: aborta si meta no tiene exactamente las mismas 411 filas esperadas.
CREATE TEMP TABLE tmp_meta_backup_recarga AS
SELECT
    m.id,
    m.id_programa,
    m.numero_meta,
    m.nombre_meta,
    m.codigo_producto,
    m.nombre_producto,
    t.unidad_medida,
    m.codigo_indicador_producto,
    m.nombre_indicador_producto
FROM meta m
JOIN tmp_meta_unidad_medida t
  ON t.numero_meta = m.numero_meta
 AND t.codigo_producto = m.codigo_producto
 AND t.codigo_indicador_producto = m.codigo_indicador_producto;

CREATE TEMP TABLE tmp_metas_rel_backup AS
SELECT id, id_meta, id_formulario, meta_proyecto
FROM metas;

DO $$
DECLARE
    v_expected INT;
    v_meta_total INT;
    v_backup_total INT;
BEGIN
    SELECT COUNT(*) INTO v_expected FROM tmp_meta_unidad_medida;
    SELECT COUNT(*) INTO v_meta_total FROM meta;
    SELECT COUNT(*) INTO v_backup_total FROM tmp_meta_backup_recarga;

    IF v_meta_total <> v_expected THEN
        RAISE EXCEPTION 'meta tiene % filas y el plan indicativo % filas. No se recarga para evitar perdida de datos.', v_meta_total, v_expected;
    END IF;

    IF v_backup_total <> v_expected THEN
        RAISE EXCEPTION 'tmp_meta_backup_recarga tiene % filas y se esperaban % (match exacto). Abortado.', v_backup_total, v_expected;
    END IF;
END $$;

-- Se eliminan primero relaciones hijas para evitar FK; luego se restauran.
DELETE FROM metas;
DELETE FROM meta;

INSERT INTO meta (
    id,
    id_programa,
    numero_meta,
    nombre_meta,
    codigo_producto,
    nombre_producto,
    unidad_medida,
    codigo_indicador_producto,
    nombre_indicador_producto
)
SELECT
    id,
    id_programa,
    numero_meta,
    nombre_meta,
    codigo_producto,
    nombre_producto,
    unidad_medida,
    codigo_indicador_producto,
    nombre_indicador_producto
FROM tmp_meta_backup_recarga
ORDER BY id;

SELECT setval(
    pg_get_serial_sequence('meta', 'id'),
    COALESCE((SELECT MAX(id) FROM meta), 1),
    true
);

INSERT INTO metas (id, id_meta, id_formulario, meta_proyecto)
SELECT
    r.id,
    r.id_meta,
    r.id_formulario,
    r.meta_proyecto
FROM tmp_metas_rel_backup r
JOIN meta m ON m.id = r.id_meta
ORDER BY r.id;

SELECT setval(
    pg_get_serial_sequence('metas', 'id'),
    COALESCE((SELECT MAX(id) FROM metas), 1),
    true
);

DO $$
DECLARE
    v_rel_src INT;
    v_rel_dst INT;
BEGIN
    SELECT COUNT(*) INTO v_rel_src FROM tmp_metas_rel_backup;
    SELECT COUNT(*) INTO v_rel_dst FROM metas;
    IF v_rel_src <> v_rel_dst THEN
        RAISE EXCEPTION 'Restauracion de metas incompleta: % restauradas de %.', v_rel_dst, v_rel_src;
    END IF;
END $$;
