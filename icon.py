from PIL import Image, ImageDraw
import os

def create_music_icon():
    # 아이콘 크기 설정
    size = (256, 256)
    padding = 40
    
    # 새 이미지 생성 (투명 배경)
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # 배경 그라데이션 (현대적인 디자인)
    for i in range(128, -1, -1):
        # 세련된 파란색 계열 그라데이션
        color = (41 - i//4, 128 - i//3, 185 - i//3, 255)
        # 원형 배경
        draw.ellipse(
            [padding + i//2, padding + i//2,
             size[0] - padding - i//2, size[1] - padding - i//2],
            fill=color
        )
    
    # 현대적인 음표 디자인
    center_x = size[0] // 2
    center_y = size[1] // 2
    
    # 음표 머리 (타원형)
    draw.ellipse(
        [center_x - 35, center_y + 10,
         center_x + 5, center_y + 40],
        fill='white'
    )
    
    # 음표 기둥
    draw.rectangle(
        [center_x + 2, center_y - 50,
         center_x + 8, center_y + 25],
        fill='white'
    )
    
    # 음표 꼬리 (곡선형 라인)
    curve_points = []
    for i in range(20):
        x = center_x + 8 + i * 1.5
        y = center_y - 50 + i * 1.2
        curve_points.append((x, y))
    
    # 곡선 그리기
    if len(curve_points) > 1:
        draw.line(curve_points, fill='white', width=3)
    
    # 작은 장식 원들
    decoration_positions = [
        (center_x - 50, center_y - 30, 10),
        (center_x + 50, center_y + 30, 8),
        (center_x - 30, center_y + 50, 6),
        (center_x + 40, center_y - 40, 7)
    ]
    
    for x, y, size in decoration_positions:
        draw.ellipse(
            [x - size, y - size,
             x + size, y + size],
            fill='white'
        )
    
    # 이미지 저장
    if not os.path.exists('assets'):
        os.makedirs('assets')
    
    # .ico 파일로 저장
    image.save('assets/music_icon.ico', format='ICO', sizes=[(256, 256)])
    # PNG 파일로도 저장
    image.save('assets/music_icon.png', format='PNG')
    
    return 'assets/music_icon.ico'

if __name__ == "__main__":
    icon_path = create_music_icon()
    print(f"아이콘이 생성되었습니다: {icon_path}")