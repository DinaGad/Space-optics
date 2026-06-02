% For hyperspectral image (Hypercube format)
hCube = hypercube('cubesat.jpg');

% For RGB or multispectral image
rgbImg = imread('cubesat.jpg');
figure;
imshow(rgbImg);
title('RGB Image');
rgbBands = [29 19 9]; % Choose bands corresponding to R, G, B wavelengths
rgbImage = colorize(hCube, 'Method', 'RGB', 'Bands', rgbBands);

figure;
imshow(rgbImage);
title('Simulated RGB from Hyperspectral Cube');
bandNumber = 5; % Example band
bandImage = hCube.DataCube(:,:,bandNumber);

figure;
imshow(mat2gray(bandImage));
title(['Band ', num2str(bandNumber)]);



