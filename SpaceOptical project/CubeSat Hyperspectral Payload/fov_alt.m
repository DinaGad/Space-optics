% This program plots the FOV of HSI against its GSD
% using different line styles, markers, and colors.

% Define altitude range (in meters)
altitude = [300, 400, 500, 600, 700, 800]; % Example altitudes

% Define Ground Sample Distance (GSD) range (in meters)
GSD = linspace(10, 100, 100); % Example GSD values

% Define constant of proportionality
k = 30; % Example value

% Initialize matrix to store effective field-of-view (FOV) values
FOV = zeros(length(altitude), length(GSD));

% Calculate FOV for each combination of altitude and GSD
for i = 1:length(altitude)
    for j = 1:length(GSD)
        FOV(i, j) = k * GSD(j) / altitude(i);
    end
end

% Define line styles and markers
lineStyles = {'-', '--', ':', '-.', '-', '--'};
markers    = {'>', 's', '^', 'd', 'x', '<'};

% Define marker face colors (6 × 3)
face_colors = [
    0.00 0.45 0.74;   % Blue
    0.85 0.33 0.10;   % Orange
    0.47 0.67 0.19;   % Green
    0.49 0.18 0.56;   % Purple
    0.93 0.69 0.13;   % Yellow
    0.30 0.30 0.30;   % Gray
];

% Define line / marker edge colors (6 × 3)
edge_colors = [
    0.00 0.00 0.00;   % Black
    0.20 0.20 0.60;   % Dark blue
    0.60 0.20 0.20;   % Dark red
    0.20 0.60 0.20;   % Dark green
    0.40 0.40 0.40;   % Dark gray
    0.10 0.10 0.10;   % Near black
];

% Plot FOV vs. GSD
figure;
hold on;
for i = 1:length(altitude)
    plot(GSD, FOV(i, :), ...
        'LineStyle', lineStyles{i}, ...
        'Marker', markers{i}, ...
        'Color', edge_colors(i, :), ...
        'MarkerEdgeColor', edge_colors(i, :), ...
        'MarkerFaceColor', face_colors(i, :), ...
        'LineWidth', 1.5, ...
        'MarkerSize', 6, ...
        'MarkerIndices', 1:10:length(GSD)); % Marker spacing
end

% Customize plot
xlabel('Ground Sampling Distance (m)', 'FontSize', 13, 'Interpreter', 'latex');
ylabel('Field of View (degrees)', 'FontSize', 13, 'Interpreter', 'latex');

legend(cellstr(num2str(altitude'/1000, 'Altitude = %.1f km')), ...
       'Location', 'best', ...
       'Interpreter', 'latex', ...
       'NumColumns', 2);

grid on;
box on;
hold off;
